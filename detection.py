import cv2
import numpy as np
import json

from scoring import score_hit
from heatmap import register_hit
from ai_classifier import classify_hit
from overlay import draw_overlay

cfg = json.load(open("config.json"))

baseline = {}
hits = []
detect_active = False


def toggle_detection():
    global detect_active, hits
    detect_active = not detect_active

    if not detect_active:
        hits = []          # clear scores when stopping
        baseline.clear()   # reset background

    return detect_active


def reset_hits():
    global hits
    hits = []


def get_hits():
    return hits


def process_frame(frame, cam_id):
    global baseline

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ---------- Baseline handling ----------
    if cam_id not in baseline:
        baseline[cam_id] = gray.copy()
        return draw_overlay(frame)

    # ---------- Detection OFF ----------
    if not detect_active:
        baseline[cam_id] = gray.copy()
        return draw_overlay(frame)

    # ---------- Detection ON ----------
    diff = cv2.absdiff(gray, baseline[cam_id])
    _, thresh = cv2.threshold(diff, cfg["threshold"], 255, cv2.THRESH_BINARY)

    thresh = cv2.morphologyEx(
        thresh, cv2.MORPH_OPEN, np.ones((3, 3))
    )

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for c in contours:
        if cv2.contourArea(c) < cfg["min_area"]:
            continue

        M = cv2.moments(c)
        if M["m00"] == 0:
            continue

        x = M["m10"] / M["m00"]
        y = M["m01"] / M["m00"]

        # Small crop for AI classifier
        x0, y0 = int(x - 8), int(y - 8)
        crop = gray[y0:y0 + 16, x0:x0 + 16]

        if crop.shape != (16, 16):
            continue

        prob = classify_hit(crop)
        if prob < 0.6:
            continue

        score, conf = score_hit(x, y)

        hits.append({
            "x": round(x, 2),
            "y": round(y, 2),
            "score": score,
            "confidence": conf,
            "ai_prob": prob
        })

        register_hit(x, y)

        cv2.circle(frame, (int(x), int(y)), 6, (0, 0, 255), 2)

    baseline[cam_id] = gray.copy()
    return draw_overlay(frame)