target = {
    "center": None,
    "px_to_mm": 1.0,
    "rings_px": []
}

def set_auto_target(geometry):
    global target
    target["center"] = geometry["center"]
    target["rings_px"] = geometry["rings_px"]

def get_target():
    return target
