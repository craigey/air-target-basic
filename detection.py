import cv2
import numpy as np
import json
import math
import time

from scoring import score_hit
from heatmap import register_hit
from ai_classifier import classify_hit
from overlay import draw_overlay
from calibration import warp_point
from shot_recorder import record_shot, save_baseline

cfg = json.load(open("config.json"))

baseline = {}
baseline_color = {}
baseline_saved = {}  # Track if baseline saved for each camera
hits = []
detect_active = False
shot_cooldown = 0
last_shot_time = 0

def toggle_detection():
    global detect_active, hits, baseline_saved
    detect_active = not detect_active

    if not detect_active:
        hits = []
        baseline.clear()
        baseline_color.clear()
        baseline_saved.clear()
    else:
        # Starting new round
        from shot_recorder import start_new_round
        start_new_round()

    return detect_active


def reset_hits():
    global hits
    hits = []
    
    # Start new round when resetting
    from shot_recorder import start_new_round
    start_new_round()


def get_hits():
    return hits


def detect_grey_marks(frame, baseline_frame):
    """
    Detect grey pellet marks on white TiO2 paint using color information.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv_baseline = cv2.cvtColor(baseline_frame, cv2.COLOR_BGR2HSV)
    
    value = hsv[:, :, 2]
    value_baseline = hsv_baseline[:, :, 2]
    
    value_diff = cv2.absdiff(value_baseline, value)
    
    grey_threshold = cfg.get("grey_threshold", 15)
    _, grey_mask = cv2.threshold(value_diff, grey_threshold, 255, cv2.THRESH_BINARY)
    
    sat = hsv[:, :, 1]
    sat_baseline = hsv_baseline[:, :, 1]
    sat_diff = cv2.absdiff(sat, sat_baseline)
    
    combined = cv2.bitwise_and(grey_mask, grey_mask, mask=(sat_diff < 30).astype(np.uint8) * 255)
    
    return combined


def process_frame(frame, cam_id):
    global baseline, baseline_color, baseline_saved, shot_cooldown, last_shot_time
    
    current_time = time.time()

    # Apply Gaussian blur
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Baseline handling
    if cam_id not in baseline:
        baseline[cam_id] = gray.copy()
        baseline_color[cam_id] = frame.copy()
        baseline_saved[cam_id] = False
        return draw_overlay(frame)

    # Detection OFF
    if not detect_active:
        baseline[cam_id] = gray.copy()
        baseline_color[cam_id] = frame.copy()
        baseline_saved[cam_id] = False
        return draw_overlay(frame)

    # Save baseline at start of round
    if not baseline_saved.get(cam_id, False):
        save_baseline(frame.copy())
        baseline_saved[cam_id] = True

    # Detection ON
    diff_gray = cv2.absdiff(gray, baseline[cam_id])
    
    if cfg.get("adaptive_threshold", True):
        thresh_gray = cv2.adaptiveThreshold(
            diff_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
    else:
        _, thresh_gray = cv2.threshold(
            diff_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
    
    if cfg.get("color_detection", True):
        grey_mask = detect_grey_marks(frame, baseline_color[cam_id])
        thresh = cv2.bitwise_or(thresh_gray, grey_mask)
    else:
        thresh = thresh_gray

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for c in contours:
        area = cv2.contourArea(c)
        
        min_area = cfg.get("min_area", 40)
        max_area = cfg.get("max_area", 400)
        
        if area < min_area or area > max_area:
            continue

        M = cv2.moments(c)
        if M["m00"] == 0:
            continue

        # RAW hit position (camera space)
        x = M["m10"] / M["m00"]
        y = M["m01"] / M["m00"]

        # AI classifier
        x0, y0 = int(x - 8), int(y - 8)
        
        if x0 < 0 or y0 < 0 or x0 + 16 >= gray.shape[1] or y0 + 16 >= gray.shape[0]:
            continue
            
        crop = gray[y0:y0 + 16, x0:x0 + 16]
        if crop.shape != (16, 16):
            continue

        prob = classify_hit(crop, c)
        min_confidence = cfg.get("min_confidence", 0.6)
        
        if prob < min_confidence:
            continue

        # Apply homography
        wx, wy = warp_point(x, y)

        # Spatial duplicate check
        too_close = False
        for prev_hit in hits[-5:]:
            if math.dist((wx, wy), (prev_hit["x"], prev_hit["y"])) < 10:
                too_close = True
                break

        if too_close:
            continue

        # Shot cooldown
        if shot_cooldown > 0:
            continue

        # Max interval check
        max_interval = cfg.get("max_shot_interval_seconds", 120)
        if last_shot_time > 0 and (current_time - last_shot_time) > max_interval:
            print(f"ℹ️ Long interval detected ({current_time - last_shot_time:.1f}s)")

        # Score using warped coordinates
        score, conf = score_hit(wx, wy, area)

        if score is None or conf < 0.5:
            continue

        # Record hit
        shot_number = len(hits) + 1
        
        hit_data = {
            "x": round(wx, 2),
            "y": round(wy, 2),
            "score": score,
            "confidence": conf,
            "ai_prob": prob,
            "area": area,
            "timestamp": current_time,
            "shot_number": shot_number
        }
        
        hits.append(hit_data)
        last_shot_time = current_time

        # Record shot image
        record_shot(frame.copy(), hit_data, shot_number)

        register_hit(wx, wy)

        # Draw detection
        if score >= 5:
            color = (0, 255, 0)  # Green for bull
        elif score > 0:
            color = (0, 0, 255)  # Red for scoring
        else:
            color = (255, 0, 0)  # Blue for miss
            
        cv2.circle(frame, (int(x), int(y)), 6, color, 2)
        cv2.putText(frame, str(score), (int(x) + 10, int(y) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        shot_cooldown = cfg.get("shot_cooldown_frames", 9)
        
        shots_per_round = cfg.get("shots_per_round", 6)
        print(f"🎯 Shot {shot_number}: Score {score} (confidence {conf:.2f})")
        
        if shot_number == shots_per_round:
            from scoring import score_distribution
            stats = score_distribution(hits)
            print(f"✅ Round complete! Total: {stats['sum']}/{stats['max_possible']} ({stats['percentage']}%)")

    if shot_cooldown > 0:
        shot_cooldown -= 1

    # Selective baseline update
    baseline_mode = cfg.get("baseline_update_mode", "selective")
    
    if shot_cooldown == 0 and baseline_mode == "selective":
        mask = np.ones(gray.shape, dtype=np.uint8) * 255
        for hit in hits[-5:]:
            cv2.circle(mask, (int(hit["x"]), int(hit["y"])), 20, 0, -1)
        
        baseline[cam_id] = np.where(mask > 0, gray, baseline[cam_id])
        
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        baseline_color[cam_id] = np.where(mask_3ch > 0, frame, baseline_color[cam_id])
        
    elif baseline_mode == "always":
        baseline[cam_id] = gray.copy()
        baseline_color[cam_id] = frame.copy()

    return draw_overlay(frame)


def get_round_summary():
    """Get summary of current round for NARPA scoring."""
    from scoring import score_distribution, format_round_score
    
    stats = score_distribution(hits)
    shots_per_round = cfg.get("shots_per_round", 6)
    
    return {
        "hits": hits,
        "total_shots": len(hits),
        "total_score": stats["sum"],
        "max_possible": shots_per_round * 5,
        "average": stats["average"],
        "complete": len(hits) >= shots_per_round,
        "formatted": format_round_score(hits),
        "percentage": stats["percentage"]
    }
