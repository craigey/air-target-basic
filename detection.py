import cv2, numpy as np, json
from scoring import score_hit
from heatmap import register_hit
from ai_classifier import classify_hit
from target_detection import detect_target
from calibration import set_auto_target
from overlay import draw_overlay

cfg = json.load(open("config.json"))

baseline = {}
hits = []
detect_active = False

def toggle_detection():
    global detect_active, hits
    detect_active = not detect_active
    if not detect_active:
        hits = []  # CLEAR hits when stopping
    return detect_active

def reset_hits():
    global hits
    hits = []

def get_hits():
    return hits

def process_frame(frame, cam_id):
    global baseline

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    geom = detect_target(gray)
    if geom:
        set_auto_target(geom)

    if cam_id not in baseline:
        baseline[cam_id] = gray.copy()
        return frame

    if not detect_active:
        baseline[cam_id] = gray.copy()
        return draw_overlay(frame)

    diff = cv2.absdiff(gray, baseline[cam_id])
    _, thresh = cv2.threshold(diff, cfg["threshold"], 255, cv2.THRESH_BINARY)

    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3,3)))

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        if cv2.contourArea(c) > cfg["min_area"]:
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue

            x = M["m10"] / M["m00"]
            y = M["m01"] / M["m00"]

            crop = gray[int(y-8):int(y+8), int(x-8):int(x+8)]
            prob = classify_hit(crop)

            if prob < 0.6:
                continue

            score, conf = score_hit(x,y)

            hits.append({
                "x": round(x,2),
                "y": round(y,2),
                "score": score,
                "confidence": conf,
                "ai_prob": prob
            })

            register_hit(x,y)

             hit_detected = True
        cv2.circle(frame, (int(x),int(y)), 6, (0,0,255), 2)

if hit_detected:
    baseline[cam_id] = gray.copy()

return draw_overlay(frame)