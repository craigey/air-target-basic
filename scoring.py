import math, json
from calibration import get_target

cfg = json.load(open("config.json"))

def score_hit(x,y):
    t = get_target()
    center = t["center"]
    if center is None:
        return None, 0

    dpx = math.dist((x,y), center)

    bull_mm = cfg["bull_mm"]
    rings_mm = cfg["rings_mm"]

    px_to_mm = bull_mm / (t["rings_px"][0] * 2)

    dmm = dpx * px_to_mm

    if dmm <= bull_mm/2:
        return 5, confidence(dmm, bull_mm/2)

    for i, r in enumerate(rings_mm):
        if dmm <= r/2:
            return 4-i, confidence(dmm, r/2)

    return 0, 0.7

def confidence(d,b):
    return round(max(0.35, 1 - (d / b)), 2)
