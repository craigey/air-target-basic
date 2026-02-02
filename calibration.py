import math
import cv2
import numpy as np
import json

cfg = json.load(open("config.json"))

_homography = None
_homography_quality = 0.0

_target = {
    "center": None,
    "rings_px": [],
    "scale_mm": None,
    "bull_hole_px": None
}

# NARPA Official Target Dimensions (mm)
BULL_HOLE_MM = cfg["bull_hole_mm"]  # 3/8" hole (9.525mm)
BULL_MM = cfg["bull_mm"]            # 1" diameter (25.4mm)
RINGS_MM = cfg["rings_mm"]          # 2", 3", 4" diameters [50.8, 76.2, 101.6]

# Optional 4" outer ring (some leagues use it for score of 1)
if cfg.get("enable_outer_ring", False):
    RINGS_MM.append(cfg.get("optional_outer_ring_mm", 127.0))


def set_calibration(data):
    """
    Set calibration from user-provided data.
    
    For NARPA targets:
    - Center: Physical center of the bull hole
    - Bull: Edge of the 1" scoring ring
    - Outer: Edge of the 4" ring (or 3" if no outer ring)
    
    data must contain:
    - center: {x,y} - center of bull hole
    - bull: {x,y} - point on bull scoring ring edge
    - outer: {x,y} - point on outer ring edge
    - src_pts: list of 4 image points (optional for homography)
    - dst_pts: list of 4 corrected points (optional for homography)
    """
    global _homography, _homography_quality, _target

    cx, cy = int(data["center"]["x"]), int(data["center"]["y"])

    # Distance from center to bull edge (1" ring)
    bull_r = math.dist(
        (cx, cy),
        (data["bull"]["x"], data["bull"]["y"])
    )

    # Distance from center to outer ring edge
    outer_r = math.dist(
        (cx, cy),
        (data["outer"]["x"], data["outer"]["y"])
    )

    # Calculate scale from BOTH bull and outer ring for better accuracy
    # Bull ring is 1" diameter (25.4mm), so radius is 12.7mm
    bull_scale = (BULL_MM / 2) / bull_r if bull_r > 0 else 0
    
    # Outer ring depends on whether 4" ring is enabled
    if cfg.get("enable_outer_ring", False):
        outer_mm = cfg.get("optional_outer_ring_mm", 127.0)  # 4" ring
    else:
        outer_mm = RINGS_MM[-1]  # 3" ring (101.6mm)
    
    outer_scale = (outer_mm / 2) / outer_r if outer_r > 0 else 0
    
    # Weight toward outer ring as it's larger and more stable
    # Use 70/30 weighting
    if bull_scale > 0 and outer_scale > 0:
        mm_per_px = (0.3 * bull_scale + 0.7 * outer_scale)
    elif outer_scale > 0:
        mm_per_px = outer_scale
    elif bull_scale > 0:
        mm_per_px = bull_scale
    else:
        print("⚠️ Warning: Invalid calibration radii")
        mm_per_px = 1.0

    # Calculate bull hole size in pixels (3/8" = 9.525mm diameter)
    bull_hole_px = (BULL_HOLE_MM / 2) / mm_per_px if mm_per_px > 0 else 0

    _target["center"] = (cx, cy)
    _target["scale_mm"] = mm_per_px
    _target["bull_hole_px"] = bull_hole_px
    
    # Calculate all ring radii in pixels
    _target["rings_px"] = [
        (mm / 2) / mm_per_px for mm in [BULL_MM] + RINGS_MM
    ]

    print(f"✅ NARPA Target Calibration:")
    print(f"   Scale: {mm_per_px:.4f} mm/px")
    print(f"   Bull ring: {bull_r:.1f}px (1\" = 25.4mm)")
    print(f"   Bull hole: {bull_hole_px:.1f}px (3/8\" = 9.525mm)")
    print(f"   Outer ring: {outer_r:.1f}px ({outer_mm/25.4:.1f}\" = {outer_mm:.1f}mm)")
    print(f"   Ring radii (px): {[f'{r:.1f}' for r in _target['rings_px']]}")

    # HOMOGRAPHY with RANSAC for robustness
    if "src_pts" in data and "dst_pts" in data and len(data["src_pts"]) >= 4:
        src = np.array(data["src_pts"], dtype=np.float32)
        dst = np.array(data["dst_pts"], dtype=np.float32)
        
        # Use RANSAC to reject outliers
        _homography, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        
        if _homography is not None and mask is not None:
            inliers = np.sum(mask)
            _homography_quality = inliers / len(mask)
            
            # Calculate reprojection error
            error = calculate_reprojection_error(_homography, src, dst)
            
            print(f"✅ Homography: {inliers}/{len(mask)} inliers, error={error:.2f}px")
            
            if _homography_quality < 0.75:
                print("⚠️ Warning: Low homography quality (<75%) - consider recalibrating")
        else:
            print("⚠️ Warning: Homography calculation failed")
    else:
        print("ℹ️ No homography points provided - using identity transform")


def calculate_reprojection_error(homography, src_pts, dst_pts):
    """
    Calculate average reprojection error to assess calibration quality.
    
    Returns:
        Average pixel error
    """
    src = np.array(src_pts, dtype=np.float32).reshape(-1, 1, 2)
    dst = np.array(dst_pts, dtype=np.float32).reshape(-1, 1, 2)
    
    projected = cv2.perspectiveTransform(src, homography)
    
    errors = np.sqrt(np.sum((projected - dst)**2, axis=2))
    return float(np.mean(errors))


def warp_point(x, y):
    """
    Transform a point from camera space to target space using homography.
    
    Args:
        x, y: Point in camera coordinates
    
    Returns:
        (wx, wy): Point in target coordinates
    """
    if _homography is None:
        return int(x), int(y)

    pt = np.array([[[x, y]]], dtype=np.float32)
    warped = cv2.perspectiveTransform(pt, _homography)
    return int(warped[0][0][0]), int(warped[0][0][1])


def get_target():
    """Get current target calibration data."""
    return _target


def get_calibration_quality():
    """Get homography quality metric (0.0-1.0)."""
    return _homography_quality


def is_calibrated():
    """Check if system is calibrated."""
    return _target["center"] is not None and _target["scale_mm"] is not None


def reset_calibration():
    """Clear all calibration data."""
    global _homography, _homography_quality, _target
    
    _homography = None
    _homography_quality = 0.0
    _target = {
        "center": None,
        "rings_px": [],
        "scale_mm": None,
        "bull_hole_px": None
    }
    print("🔄 Calibration reset")
