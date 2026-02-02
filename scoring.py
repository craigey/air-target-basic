import math
import json
from calibration import get_target

cfg = json.load(open("config.json"))

# NARPA Scoring Rules:
# Bull (1" ring) = 5
# Ring 1 (2" ring) = 4  
# Ring 2 (3" ring) = 3
# Ring 3 (4" ring) = 2
# Outside all rings = 0
# Optional: 5" ring = 1 (if enabled)
# Bull hole (no mark) = 5.1 (if enabled)

def score_hit(x, y, area=None):
    """
    Calculate score based on NARPA rules.
    
    NARPA Scoring:
    - Bull (1" ring): 5 points
    - Ring 1 (2"): 4 points
    - Ring 2 (3"): 3 points
    - Ring 3 (4"): 2 points
    - Outside: 0 points
    - Optional Ring 4 (5"): 1 point (if enabled)
    - Bull hole (pellet through hole): 5.1 points (if enabled)
    
    Split shots: Majority of pellet mark determines score (scores higher)
    
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
    
    # Get pellet radius in pixels for calculations
    pellet_px = pellet_mm / mm_per_px

    # Check for bull hole shot (pellet through the 3/8" hole with no mark)
    # This is rare but scores 5.1 in some leagues
    if cfg.get("enable_bull_hole_bonus", False) and t["bull_hole_px"]:
        # If very small area near center, might be bull hole shot
        if area and area < 30 and dpx < t["bull_hole_px"]:
            return cfg.get("bull_hole_score", 5.1), 1.0

    # NARPA scoring with split shot logic:
    # Use the CENTER of the pellet mark for scoring
    # This simulates "majority of pellet" rule since center represents
    # where most of the pellet mass hit
    
    # Bull (1" ring = 25.4mm diameter) - Score 5
    bull_radius_mm = cfg["bull_mm"] / 2
    if dmm <= bull_radius_mm:
        return 5, confidence(dmm, bull_radius_mm)
    
    # Scoring rings: 2", 3", 4" (and optional 5")
    # Score: 4, 3, 2 (and optional 1)
    rings_mm = cfg["rings_mm"]
    base_score = 4
    
    for i, ring_mm in enumerate(rings_mm):
        ring_radius_mm = ring_mm / 2
        
        if dmm <= ring_radius_mm:
            score = base_score - i
            
            # Handle optional outer ring (4" ring scores 1 instead of 2)
            if cfg.get("enable_outer_ring", False) and i == len(rings_mm) - 1:
                score = 1
            
            return score, confidence(dmm, ring_radius_mm)
    
    # Outside all rings - Score 0
    return 0, 0.7


def confidence(distance_mm, boundary_mm):
    """
    Calculate confidence based on how close to ring boundary.
    
    For NARPA split shots: confidence decreases near boundaries
    since "majority rule" becomes harder to judge.
    
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
    # Split shots are ambiguous, so confidence drops faster near edges
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
        return {
            "total": 0,
            "scores": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0},
            "average": 0.0,
            "sum": 0,
            "bull_holes": 0
        }
    
    scores = [h["score"] for h in hits]
    score_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0}
    bull_holes = 0
    
    for s in scores:
        if s == 5.1:
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
        "percentage": round((total_score / (len(hits) * 5)) * 100, 1) if len(hits) > 0 else 0
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
    
    output = f"Round Score: {stats['sum']}/{stats['max_possible']}\n"
    output += f"Shots: {' + '.join(individual)}\n"
    output += f"Average: {stats['average']}\n"
    
    if stats['bull_holes'] > 0:
        output += f"Bull Holes: {stats['bull_holes']} (5.1 bonus)\n"
    
    # Warn if not full round
    if len(hits) < shots_per_round:
        output += f"⚠️ Incomplete round ({len(hits)}/{shots_per_round} shots)\n"
    
    return output


def is_split_shot(distance_mm, boundary_mm, pellet_mm):
    """
    Determine if a shot is potentially a split shot (on the line).
    
    A split shot is when the pellet mark touches a scoring ring boundary.
    In NARPA rules, majority of pellet determines score (scores higher).
    
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
