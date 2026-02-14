import math
import json
from calibration import get_target

cfg = json.load(open("config.json"))

# Runtime configuration (can be changed via API)
_scoring_config = {
    "use_4_ring": cfg.get("use_4_ring_scoring", True),
    "enable_bull_hole_bonus": cfg.get("enable_bull_hole_bonus", False),
    "bull_hole_score": cfg.get("bull_hole_score", 5.1)
}

def set_scoring_config(use_4_ring=None, enable_bull_hole_bonus=None):
    """
    Update scoring configuration at runtime.
    
    Args:
        use_4_ring: True for 4-ring (1pt outer), False for 3-ring (no outer)
        enable_bull_hole_bonus: True to enable 5.1 scoring for bull holes
    """
    global _scoring_config
    
    if use_4_ring is not None:
        _scoring_config["use_4_ring"] = use_4_ring
    
    if enable_bull_hole_bonus is not None:
        _scoring_config["enable_bull_hole_bonus"] = enable_bull_hole_bonus
    
    # Save to config file
    cfg["use_4_ring_scoring"] = _scoring_config["use_4_ring"]
    cfg["enable_bull_hole_bonus"] = _scoring_config["enable_bull_hole_bonus"]
    
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)
    
    print(f"✅ Scoring config updated: 4-ring={_scoring_config['use_4_ring']}, "
          f"bull hole bonus={_scoring_config['enable_bull_hole_bonus']}")
    
    return _scoring_config


def get_scoring_config():
    """Get current scoring configuration."""
    return _scoring_config.copy()


def score_hit(x, y, area=None):
    """
    Calculate score based on NARPA rules with runtime configuration.
    
    NARPA 4-Ring Scoring (default):
    - Bull (1" ring): 5 points
    - Ring 1 (2"): 4 points
    - Ring 2 (3"): 3 points
    - Ring 3 (4"): 2 points
    - Ring 4 (5"): 1 point
    - Outside: 0 points
    
    NARPA 3-Ring Scoring (optional):
    - Bull (1" ring): 5 points
    - Ring 1 (2"): 4 points
    - Ring 2 (3"): 3 points
    - Ring 3 (4"): 2 points
    - Outside: 0 points
    
    Bull Hole Bonus (optional):
    - Pellet through hole: 5.1 points
    
    Args:
        x, y: Hit position in target space (after homography)
        area: Contour area (optional, for bull hole detection)
    
    Returns:
        (score, confidence): Score value (0-5.1) and confidence (0.0-1.0)
    """
    t = get_target()
    center = t["center"]
    
    if center is None:
        return None, 0.0

    # Distance from center in pixels
    dpx = math.dist((x, y), center)

    # Get calibration data
    pellet_mm = cfg["pellet_mm"] / 2  # pellet radius in mm
    mm_per_px = t["scale_mm"]
    
    if mm_per_px is None or mm_per_px <= 0:
        print("⚠️ Warning: Invalid scale calibration")
        return None, 0.0

    # Convert distance to millimeters
    dmm = dpx * mm_per_px

    # Check for bull hole shot (pellet through the 3/8" hole with no mark)
    if _scoring_config["enable_bull_hole_bonus"] and t["bull_hole_px"]:
        # If very small area near center, might be bull hole shot
        if area and area < 30 and dpx < t["bull_hole_px"]:
            return _scoring_config["bull_hole_score"], 1.0

    # NARPA scoring with split shot logic:
    # Use the CENTER of the pellet mark for scoring
    
    # Bull (1" ring = 25.4mm diameter) - Score 5
    bull_radius_mm = cfg["bull_mm"] / 2
    if dmm <= bull_radius_mm:
        return 5, confidence(dmm, bull_radius_mm)
    
    # Determine which rings to use based on configuration
    if _scoring_config["use_4_ring"]:
        # 4-ring scoring: 2", 3", 4", 5" = scores 4, 3, 2, 1
        rings_mm = cfg["rings_mm"]  # All 4 rings
        scores = [4, 3, 2, 1]
    else:
        # 3-ring scoring: 2", 3", 4" = scores 4, 3, 2
        rings_mm = cfg["rings_mm"][:3]  # First 3 rings only
        scores = [4, 3, 2]
    
    for i, ring_mm in enumerate(rings_mm):
        ring_radius_mm = ring_mm / 2
        
        if dmm <= ring_radius_mm:
            score = scores[i]
            return score, confidence(dmm, ring_radius_mm)
    
    # Outside all rings - Score 0
    return 0, 0.7


def confidence(distance_mm, boundary_mm):
    """
    Calculate confidence based on how close to ring boundary.
    
    For NARPA split shots: confidence decreases near boundaries
    since "majority rule" becomes harder to judge.
    
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
    if relative_pos > 0.85:
        # Very close to boundary - low confidence (split shot zone)
        conf = 0.4
    elif relative_pos > 0.7:
        # Approaching boundary - medium confidence
        conf = 0.6
    else:
        # Well within ring - high confidence
        conf = max(0.35, 1.0 - (relative_pos * 0.5))
    
    return round(conf, 2)


def score_distribution(hits):
    """
    Calculate score distribution statistics for NARPA rules.
    
    Args:
        hits: List of hit dictionaries
    
    Returns:
        Dictionary with score statistics
    """
    if not hits:
        max_rings = 4 if _scoring_config["use_4_ring"] else 3
        score_dict = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0} if max_rings == 4 else {5: 0, 4: 0, 3: 0, 2: 0, 0: 0}
        
        return {
            "total": 0,
            "scores": score_dict,
            "average": 0.0,
            "sum": 0,
            "bull_holes": 0,
            "max_rings": max_rings
        }
    
    scores = [h["score"] for h in hits]
    
    # Initialize score counts based on current configuration
    if _scoring_config["use_4_ring"]:
        score_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0}
    else:
        score_counts = {5: 0, 4: 0, 3: 0, 2: 0, 0: 0}
    
    bull_holes = 0
    
    for s in scores:
        if s == _scoring_config["bull_hole_score"]:
            bull_holes += 1
            score_counts[5] = score_counts.get(5, 0) + 1  # Count as 5 for distribution
        else:
            score_counts[int(s)] = score_counts.get(int(s), 0) + 1
    
    # Calculate total (5.1 counts as 5.1 for total)
    total_score = sum(scores)
    
    return {
        "total": len(hits),
        "scores": score_counts,
        "average": round(total_score / len(scores), 2),
        "sum": round(total_score, 1),
        "bull_holes": bull_holes,
        "max_possible": len(hits) * 5,
        "percentage": round((total_score / (len(hits) * 5)) * 100, 1) if len(hits) > 0 else 0,
        "max_rings": 4 if _scoring_config["use_4_ring"] else 3
    }


def format_round_score(hits):
    """
    Format a round score for display (NARPA typically 5-6 shots).
    
    Args:
        hits: List of hit dictionaries
    
    Returns:
        Formatted string with score breakdown
    """
    stats = score_distribution(hits)
    shots_per_round = cfg.get("shots_per_round", 6)
    
    # Individual scores
    individual = [str(h["score"]) for h in hits]
    
    ring_mode = "4-ring" if _scoring_config["use_4_ring"] else "3-ring"
    
    output = f"Round Score ({ring_mode}): {stats['sum']}/{stats['max_possible']}\n"
    output += f"Shots: {' + '.join(individual)}\n"
    output += f"Average: {stats['average']}\n"
    output += f"Percentage: {stats['percentage']}%\n"
    
    if stats['bull_holes'] > 0:
        output += f"Bull Holes: {stats['bull_holes']} ({_scoring_config['bull_hole_score']} bonus)\n"
    
    # Warn if not full round
    if len(hits) < shots_per_round:
        output += f"⚠️ Incomplete round ({len(hits)}/{shots_per_round} shots)\n"
    
    return output


def is_split_shot(distance_mm, boundary_mm, pellet_mm):
    """
    Determine if a shot is potentially a split shot (on the line).
    
    Args:
        distance_mm: Distance from center to pellet center
        boundary_mm: Ring boundary radius
        pellet_mm: Pellet diameter
    
    Returns:
        True if potentially a split shot
    """
    pellet_radius_mm = pellet_mm / 2
    
    # Check if pellet edge crosses the boundary
    closest_edge = distance_mm - pellet_radius_mm
    farthest_edge = distance_mm + pellet_radius_mm
    
    # Split if boundary is between edges
    return closest_edge < boundary_mm < farthest_edge
