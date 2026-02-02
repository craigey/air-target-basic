import cv2
import numpy as np
import json
import math

from scoring import score_hit
from heatmap import register_hit
from ai_classifier import classify_hit
from overlay import draw_overlay
from calibration import warp_point

cfg = json.load(open("config.json"))

baseline = {}
baseline_color = {}  # For color-based detection
hits = []
detect_active = False
shot_cooldown = 0

def toggle_detection():
    global detect_active, hits
    detect_active = not detect_active

    if not detect_active:
        hits = []          # clear scores when stopping
        baseline.clear()   # reset background
        baseline_color.clear()

    return detect_active


def reset_hits():
    global hits
    hits = []


def get_hits():
    return hits


def detect_grey_marks(frame, baseline_frame):
    """
    Detect grey pellet marks on white TiO2 paint using color information.
    Grey marks have lower saturation and value than white background.
    """
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv_baseline = cv2.cvtColor(baseline_frame, cv2.COLOR_BGR2HSV)
    
    # Extract Value (brightness) channel - grey marks are darker
    value = hsv[:, :, 2]
    value_baseline = hsv_baseline[:, :, 2]
    
    # Detect darkening (grey marks on white)
    value_diff = cv2.absdiff(value_baseline, value)
    
    # Grey marks: significant darkening (>15 on 0-255 scale)
    _, grey_mask = cv2.threshold(value_diff, cfg.get("grey_threshold", 15), 255, cv2.THRESH_BINARY)
    
    # Also check saturation - grey is low saturation
    sat = hsv[:, :, 1]
    sat_baseline = hsv_baseline[:, :, 1]
    sat_diff = cv2.absdiff(sat, sat_baseline)
    
    # Combine: darkening AND low saturation change
    combined = cv2.bitwise_and(grey_mask, grey_mask, mask=(sat_diff < 30).astype(np.uint8) * 255)
    
    return combined


def process_frame(frame, cam_id):
    global baseline, baseline_color, shot_cooldown

    # Apply Gaussian blur to reduce noise
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ---------- Baseline handling ----------
    if cam_id not in baseline:
        baseline[cam_id] = gray.copy()
        baseline_color[cam_id] = frame.copy()
        return draw_overlay(frame)

    # ---------- Detection OFF ----------
    if not detect_active:
        baseline[cam_id] = gray.copy()
        baseline_color[cam_id] = frame.copy()
        return draw_overlay(frame)

    # ---------- Detection ON ----------
    
    # METHOD 1: Traditional grayscale difference
    diff_gray = cv2.absdiff(gray, baseline[cam_id])
    
    # Use adaptive thresholding if enabled, otherwise OTSU
    if cfg.get("adaptive_threshold", True):
        # Adaptive threshold works better with varying lighting
        thresh_gray = cv2.adaptiveThreshold(
            diff_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
    else:
        # OTSU automatically finds optimal threshold
        _, thresh_gray = cv2.threshold(
            diff_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
    
    # METHOD 2: Color-based grey mark detection
    if cfg.get("color_detection", True):
        grey_mask = detect_grey_marks(frame, baseline_color[cam_id])
        # Combine both methods - either can detect
        thresh = cv2.bitwise_or(thresh_gray, grey_mask)
    else:
        thresh = thresh_gray

    # Morphological operations to clean up noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for c in contours:
        area = cv2.contourArea(c)
        
        # Check area bounds
        if area < cfg.get("min_area", 40):
            continue
        if area > cfg.get("max_area", 400):
            continue

        M = cv2.moments(c)
        if M["m00"] == 0:
            continue

        # RAW hit position (camera space)
        x = M["m10"] / M["m00"]
        y = M["m01"] / M["m00"]

        # ---------- AI classifier uses RAW coords ----------
        x0, y0 = int(x - 8), int(y - 8)
        
        # Ensure crop is within bounds
        if x0 < 0 or y0 < 0 or x0 + 16 >= gray.shape[1] or y0 + 16 >= gray.shape[0]:
            continue
            
        crop = gray[y0:y0 + 16, x0:x0 + 16]

        if crop.shape != (16, 16):
            continue

        # Check circularity and get AI probability
        prob = classify_hit(crop, c)
        if prob < cfg.get("min_confidence", 0.6):
            continue

        # APPLY HOMOGRAPHY (camera → target space)
        wx, wy = warp_point(x, y)

        # --- Spatial duplicate check ---
        # Don't detect the same hole twice (within 10px)
        too_close = False
        for prev_hit in hits[-5:]:  # Check last 5 hits
            if math.dist((wx, wy), (prev_hit["x"], prev_hit["y"])) < 10:
                too_close = True
                break

        if too_close:
            continue

        # --- Shot cooldown gating ---
        if shot_cooldown > 0:
            continue

        # Score using warped coordinates
        score, conf = score_hit(wx, wy)

        # Reject invalid scores
        if score is None or conf < 0.5:
            continue

        hits.append({
            "x": round(wx, 2),
            "y": round(wy, 2),
            "score": score,
            "confidence": conf,
            "ai_prob": prob
        })

        register_hit(wx, wy)

        # Draw detection circle on original frame
        cv2.circle(frame, (int(x), int(y)), 6, (0, 0, 255), 2)

        # Lock out further detections for configured frames
        shot_cooldown = cfg.get("shot_cooldown_frames", 15)

    # Decrement cooldown each frame
    if shot_cooldown > 0:
        shot_cooldown -= 1

    # Selective baseline update - avoid areas with recent hits
    if shot_cooldown == 0 and cfg.get("baseline_update_mode", "selective") == "selective":
        # Create a mask excluding recent hit locations
        mask = np.ones(gray.shape, dtype=np.uint8) * 255
        for hit in hits[-5:]:  # Last 5 hits
            # Convert back to camera space for masking
            # (Approximate - ideally would inverse-warp, but this works)
            cv2.circle(mask, (int(hit["x"]), int(hit["y"])), 20, 0, -1)
        
        # Update only non-hit areas
        baseline[cam_id] = np.where(mask > 0, gray, baseline[cam_id])
        
        # Update color baseline similarly
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        baseline_color[cam_id] = np.where(mask_3ch > 0, frame, baseline_color[cam_id])
    elif cfg.get("baseline_update_mode", "selective") == "always":
        # Original behavior - continuous update
        baseline[cam_id] = gray.copy()
        baseline_color[cam_id] = frame.copy()
    # else: "never" mode - don't update

    return draw_overlay(frame)
