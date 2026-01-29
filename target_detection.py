import cv2
import numpy as np

target_geometry = None

def detect_target(gray):
    global target_geometry

    blurred = cv2.medianBlur(gray, 5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=80,
        param1=60,
        param2=30,
        minRadius=15,
        maxRadius=200
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))
        circles = sorted(circles[0], key=lambda c: c[2])

        bull = circles[0]
        rings = circles[1:5]

        target_geometry = {
            "center": (bull[0], bull[1]),
            "bull_radius_px": bull[2],
            "rings_px": [r[2] for r in rings]
        }

    return target_geometry
