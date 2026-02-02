import math
import cv2
import numpy as np

_homography = None
_homography_quality = 0.0

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
    Set calibration from user-provided data.
    
    data must contain:
    - center: {x,y}
    - bull: {x,y}
    - outer: {x,y}
    - src_pts: list of 4 image points (optional for homography)
    - dst_pts: list of 4 corrected points (optional for homography)
    """
    global _homography, _homography_quality, _target

    cx, cy = int(data["center"]["x"]), int(data["center"]["y"])

    bull_r = math.dist(
        (cx, cy),
        (data["bull"]["x"], data["bull"]["y"])
    )

    outer_r = math.dist(
        (cx, cy),
        (data["outer"]["x"], data["outer"]["y"])
    )

    # Calculate scale from BOTH bull and outer ring for better accuracy
    bull_scale = (BULL_DIAM / 2) / bull_r if bull_r > 0 else 0
    outer_scale = (RINGS_MM[-1] / 2) / outer_r if outer_r > 0 else 0
    
    # Average the two scales (weight toward outer ring as it's larger/more stable)
    if bull_scale > 0 and outer_scale > 0:
        mm_per_px = (0.3 * bull_scale + 0.7 * outer_scale)
    elif outer_scale > 0:
        mm_per_px = outer_scale
    elif bull_scale > 0:
        mm_per_px = bull_scale
    else:
        print("⚠️ Warning: Invalid calibration radii")
        mm_per_px = 1.0

    _target["center"] = (cx, cy)
    _target["scale_mm"] = mm_per_px
    _target["rings_px"] = [
        (mm / 2) / mm_per_px for mm in RINGS_MM
    ]

    print(f"✅ Calibration: scale={mm_per_px:.4f} mm/px")
    print(f"   Bull radius: {bull_r:.1f}px, Outer radius: {outer_r:.1f}px")

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
                print("⚠️ Warning: Low homography quality - consider recalibrating")
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


def reset_calibration():
    """Clear all calibration data."""
    global _homography, _homography_quality, _target
    
    _homography = None
    _homography_quality = 0.0
    _target = {
        "center": None,
        "rings_px": [],
        "scale_mm": None
    }
    print("🔄 Calibration reset")
