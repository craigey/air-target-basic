import cv2
from calibration import get_target
from heatmap import get_heat, is_enabled

def draw_overlay(frame):
    t = get_target()
    if t["center"] is None:
        return frame

    cx, cy = t["center"]

    # Bull
    cv2.circle(frame, (cx,cy), int(t["rings_px"][0]/3), (255,255,255), 2)

    # Rings
    for r in t["rings_px"]:
        cv2.circle(frame, (cx,cy), int(r), (0,215,255), 2)

    # Center dot
    cv2.circle(frame, (cx,cy), 2, (0,0,255), -1)

    # ---- Heatmap overlay ----
    if is_enabled():
        for (x, y) in get_heat():
            cv2.circle(frame, (int(x), int(y)), 2, (0, 0, 255), -1)

    return frame
    