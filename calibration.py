import math

_target = {
    "center": None,
    "rings_px": [],
    "scale_mm": None
}

# REAL dimensions (mm)
BULL_DIAM = 9.525
RINGS_MM = [25.4, 50.8, 76.2, 101.6]

def set_calibration(data):
    cx, cy = int(data["center"]["x"]), int(data["center"]["y"])

    bull_r = math.dist(
        (cx,cy),
        (data["bull"]["x"], data["bull"]["y"])
    )

    outer_r = math.dist(
        (cx,cy),
        (data["outer"]["x"], data["outer"]["y"])
    )

    mm_per_px = (RINGS_MM[-1]/2) / outer_r

    _target["center"] = (cx,cy)
    _target["scale_mm"] = mm_per_px
    _target["rings_px"] = [
        (mm/2)/mm_per_px for mm in RINGS_MM
    ]

def get_target():
    return _target