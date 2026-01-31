import math

# Global target state
_target = {
    "center": None,
    "rings_px": []
}

def set_auto_target(geom):
    """
    geom = {
        "center": (x,y),
        "rings_px": [r_bull, r1, r2, r3, r4]
    }
    """
    global _target
    _target["center"] = geom["center"]
    _target["rings_px"] = geom["rings_px"]

def set_calibration(data):
    """
    Manual calibration from UI
    """
    global _target
    _target["center"] = tuple(data["center"])
    _target["rings_px"] = data["rings_px"]

def get_target():
    return _target