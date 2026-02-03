import math
import cv2
import numpy as np
import json

cfg = json.load(open("config.json"))

# Store calibration per camera
_homography = {}
_homography_quality = {}
_target = {}

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
    - camera_id: Camera ID (optional, defaults to 0)
    - center: {x,y} - center of bull hole
    - bull: {x,y} - point on bull scoring ring edge
    - outer: {x,y} - point on outer ring edge
    - src_pts: list of 4 image points (optional for homography)
    - dst_pts: list of 4 corrected points (optional for homography)
    """
    global _homography, _homography_quality, _target
    
    cam_id = data.get("camera_id", 0)

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

    # Initialize camera target if not exists
    if cam_id not in _target:
        _target[cam_id] = {}
    
    _target[cam_id]["center"] = (cx, cy)
    _target[cam_id]["scale_mm"] = mm_per_px
    _target[cam_id]["bull_hole_px"] = bull_hole_px
    
    # Calculate all ring radii in pixels
    _target[cam_id]["rings_px"] = [
        (mm / 2) / mm_per_px for mm in [BULL_MM] + RINGS_MM
    ]

    print(f"✅ NARPA Target Calibration (Camera {cam_id}):")
    print(f"   Scale: {mm_per_px:.4f} mm/px")
    print(f"   Bull ring: {bull_r:.1f}px (1\" = 25.4mm)")
    print(f"   Bull hole: {bull_hole_px:.1f}px (3/8\" = 9.525mm)")
    print(f"   Outer ring: {outer_r:.1f}px ({outer_mm/25.4:.1f}\" = {outer_mm:.1f}mm)")
    print(f"   Ring radii (px): {[f'{r:.1f}' for r in _target[cam_id]['rings_px']]}")

    # HOMOGRAPHY with RANSAC for robustness
    if "src_pts" in data and "dst_pts" in data and len(data["src_pts"]) >= 4:
        src = np.array(data["src_pts"], dtype=np.float32)
        dst = np.array(data["dst_pts"], dtype=np.float32)
        
        # Use RANSAC to reject outliers
        H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        _homography[cam_id] = H
        
        if H is not None and mask is not None:
            inliers = np.sum(mask)
            _homography_quality[cam_id] = inliers / len(mask)
            
            # Calculate reprojection error
            error = calculate_reprojection_error(_homography[cam_id], src, dst)
            
            print(f"✅ Homography: {inliers}/{len(mask)} inliers, error={error:.2f}px")
            
            if _homography_quality[cam_id] < 0.75:
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


def warp_point(x, y, cam_id=0):
    """
    Transform a point from camera space to target space using homography.
    
    Args:
        x, y: Point in camera coordinates
        cam_id: Camera ID (default 0)
    
    Returns:
        (wx, wy): Point in target coordinates
    """
    if cam_id not in _homography or _homography[cam_id] is None:
        return int(x), int(y)

    pt = np.array([[[x, y]]], dtype=np.float32)
    warped = cv2.perspectiveTransform(pt, _homography[cam_id])
    return int(warped[0][0][0]), int(warped[0][0][1])


def get_target(cam_id=0):
    """Get current target calibration data for specific camera."""
    if cam_id not in _target:
        # Return default empty target
        return {
            "center": None,
            "rings_px": [],
            "scale_mm": None,
            "bull_hole_px": None
        }
    return _target[cam_id]


def get_calibration_quality(cam_id=0):
    """Get homography quality metric (0.0-1.0) for specific camera."""
    return _homography_quality.get(cam_id, 0.0)


def is_calibrated(cam_id=0):
    """Check if system is calibrated for specific camera."""
    if cam_id not in _target:
        return False
    return _target[cam_id].get("center") is not None and _target[cam_id].get("scale_mm") is not None


def reset_calibration(cam_id=None):
    """
    Clear calibration data.
    
    Args:
        cam_id: Camera ID to reset, or None to reset all cameras
    """
    global _homography, _homography_quality, _target
    
    if cam_id is None:
        # Reset all cameras
        _homography = {}
        _homography_quality = {}
        _target = {}
        print("🔄 All calibrations reset")
    else:
        # Reset specific camera
        if cam_id in _homography:
            del _homography[cam_id]
        if cam_id in _homography_quality:
            del _homography_quality[cam_id]
        if cam_id in _target:
            del _target[cam_id]
        print(f"🔄 Calibration reset for camera {cam_id}")
