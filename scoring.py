import math
import json
from calibration import get_target

cfg = json.load(open("config.json"))

def score_hit(x, y):
    """
    Calculate score based on distance from target center.
    
    Args:
        x, y: Hit position in target space (after homography)
    
    Returns:
        (score, confidence): Score value (0-5) and confidence (0.0-1.0)
    """
    t = get_target()
    center = t["center"]
    
    if center is None:
        return None, 0.0

    # Distance in pixels
    dpx = math.dist((x, y), center)

    # Get calibration data
    pellet_mm = cfg["pellet_mm"] / 2  # radius
    bull_mm = cfg["bull_mm"]
    rings_mm = cfg["rings_mm"]

    # Use the correctly calibrated scale factor
    mm_per_px = t["scale_mm"]
    
    if mm_per_px is None or mm_per_px <= 0:
        print("⚠️ Warning: Invalid scale calibration")
        return None, 0.0

    # Convert distance to millimeters
    dmm = dpx * mm_per_px

    # Score based on closest edge of pellet to ring centers
    # (pellet can "cut the line" to score)
    effective_distance = dmm - pellet_mm

    # Bull's eye (5 points)
    if effective_distance <= bull_mm / 2:
        return 5, confidence(dmm, bull_mm / 2)

    # Scoring rings (4, 3, 2, 1 points)
    for i, ring_mm in enumerate(rings_mm):
        if effective_distance <= ring_mm / 2:
            score = 4 - i
            return score, confidence(dmm, ring_mm / 2)

    # Outside all rings (0 points)
    return 0, 0.7


def confidence(distance_mm, boundary_mm):
    """
    Calculate confidence based on how close to ring boundary.
    
    Higher confidence when well within a ring.
    Lower confidence when near boundaries (more uncertainty).
    
    Args:
        distance_mm: Actual distance from center in mm
        boundary_mm: Ring boundary radius in mm
    
    Returns:
        Confidence value (0.35-1.0)
    """
    if boundary_mm <= 0:
        return 0.5
    
    # Calculate relative position within ring
    # 0.0 = at center, 1.0 = at boundary
    relative_pos = distance_mm / boundary_mm
    
    # High confidence near center, drops as approaching boundary
    conf = max(0.35, 1.0 - (relative_pos * 0.5))
    
    return round(conf, 2)


def score_distribution(hits):
    """
    Calculate score distribution statistics.
    
    Args:
        hits: List of hit dictionaries
    
    Returns:
        Dictionary with score statistics
    """
    if not hits:
        return {
            "total": 0,
            "scores": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0},
            "average": 0.0,
            "sum": 0
        }
    
    scores = [h["score"] for h in hits]
    score_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0}
    
    for s in scores:
        score_counts[s] = score_counts.get(s, 0) + 1
    
    return {
        "total": len(hits),
        "scores": score_counts,
        "average": round(sum(scores) / len(scores), 2),
        "sum": sum(scores)
    }
