import cv2
from calibration import get_target

def draw_overlay(frame):
    t = get_target()
    if t["center"] is None:
        return frame

    cx, cy = t["center"]

    cv2.circle(frame, (cx,cy), int(t["rings_px"][0]), (255,255,0), 2)

    for r in t["rings_px"]:
        cv2.circle(frame, (cx,cy), int(r), (0,255,255), 2)

    cv2.circle(frame, (cx,cy), 3, (0,0,255), -1)

    return frame
