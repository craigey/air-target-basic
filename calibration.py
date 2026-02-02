import math
import cv2
import numpy as np

_homography = None

_target = {
    "center": None,
    "rings_px": [],
    "scale_mm": None
}

# REAL dimensions (mm)
BULL_DIAM = 9.525
RINGS_MM = [25.4, 50.8, 76.2, 101.6]

def set_calibration(data):
    """
    data must contain:
    - center: {x,y}
    - bull: {x,y}
    - outer: {x,y}
    - src_pts: list of 4 image points
    - dst_pts: list of 4 corrected points
    """
    global _homography

    cx, cy = int(data["center"]["x"]), int(data["center"]["y"])

    bull_r = math.dist(
        (cx, cy),
        (data["bull"]["x"], data["bull"]["y"])
    )

    outer_r = math.dist(
        (cx, cy),
        (data["outer"]["x"], data["outer"]["y"])
    )

    mm_per_px = (RINGS_MM[-1] / 2) / outer_r

    _target["center"] = (cx, cy)
    _target["scale_mm"] = mm_per_px
    _target["rings_px"] = [
        (mm / 2) / mm_per_px for mm in RINGS_MM
    ]

    # 🔹 HOMOGRAPHY
    if "src_pts" in data and "dst_pts" in data:
        src = np.array(data["src_pts"], dtype=np.float32)
        dst = np.array(data["dst_pts"], dtype=np.float32)
        _homography, _ = cv2.findHomography(src, dst)

def warp_point(x, y):
    if _homography is None:
        return int(x), int(y)

    pt = np.array([[[x, y]]], dtype=np.float32)
    warped = cv2.perspectiveTransform(pt, _homography)
    return int(warped[0][0][0]), int(warped[0][0][1])

def get_target():
    return _target