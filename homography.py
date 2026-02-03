import cv2
import numpy as np

H = None

def set_homography(src_pts, dst_size=(800, 800)):
    """
    Set perspective transformation matrix.
    
    Args:
        src_pts: 4 points in source image
        dst_size: Output size (width, height)
    """
    global H
    dst_pts = np.array([
        [0, 0],
        [dst_size[0], 0],
        [dst_size[0], dst_size[1]],
        [0, dst_size[1]]
    ], dtype=np.float32)

    H = cv2.getPerspectiveTransform(
        np.array(src_pts, dtype=np.float32),
        dst_pts
    )
    print(f"✅ Homography matrix set for {dst_size[0]}x{dst_size[1]} output")


def warp(frame):
    """
    Apply perspective warp to frame if homography is set.
    
    Args:
        frame: Input frame
    
    Returns:
        Warped frame or original if no homography set
    """
    if H is None:
        return frame
    
    try:
        return cv2.warpPerspective(frame, H, (800, 800))
    except Exception as e:
        print(f"⚠️ Homography warp failed: {e}")
        return frame


def reset_homography():
    """Clear homography matrix."""
    global H
    H = None
    print("🔄 Homography reset")


def get_homography():
    """Get current homography matrix."""
    return H
