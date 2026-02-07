import cv2
from calibration import get_target
from heatmap import get_heatmap_normalized, is_heatmap_enabled

def draw_overlay(frame, cam_id=0):
    """Draw target rings and heatmap overlay on frame."""
    t = get_target(cam_id)
    if t.get("center") is None:
        return frame

    cx, cy = t["center"]

    # Bull hole (inner circle)
    bull_hole_radius = int(t.get("bull_hole_px", 5))
    cv2.circle(frame, (cx, cy), bull_hole_radius, (255, 255, 255), 2)

    # Scoring rings
    for r in t.get("rings_px", []):
        cv2.circle(frame, (cx, cy), int(r), (0, 215, 255), 2)

    # Center dot
    cv2.circle(frame, (cx, cy), 2, (0, 0, 255), -1)

    # Heatmap overlay
    if is_heatmap_enabled():
        try:
            heatmap = get_heatmap_normalized()
            for point in heatmap:
                # Handle different heatmap formats
                if isinstance(point, (list, tuple)):
                    if len(point) >= 2:
                        x, y = point[0], point[1]
                        cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 255), -1)
        except Exception as e:
            # Silently fail if heatmap has issues
            pass

    return frame