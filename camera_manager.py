import cv2
import time
from detection import process_frame
from homography import warp

caps = {}
exposure_locked = {}

def init_cameras(camera_ids=[0]):
    """
    Initialize USB cameras with optimized settings.
    camera_ids: list of integers (default [0])
    """
    global caps, exposure_locked

    for cam_id in camera_ids:
        cap = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Set to manual exposure mode
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 1 = Manual mode, 3 = Auto
        
        if not cap.isOpened():
            raise RuntimeError(f"❌ Cannot open camera {cam_id}")

        caps[cam_id] = cap
        exposure_locked[cam_id] = False
        
        print(f"✅ Initialized camera {cam_id}")

    print(f"✅ All cameras ready: {list(caps.keys())}")


def lock_exposure(cam_id=0, stabilization_frames=30):
    """
    Lock camera exposure to prevent auto-adjustment during shooting.
    
    This is critical for consistent frame differencing!
    
    Args:
        cam_id: Camera ID to lock
        stabilization_frames: Number of frames to capture before locking
    
    Returns:
        True if successful, False otherwise
    """
    cap = caps.get(cam_id)
    if cap is None:
        print(f"⚠️ Camera {cam_id} not initialized")
        return False
    
    # First, enable auto-exposure to let camera adjust
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)  # Auto mode
    
    print(f"📸 Stabilizing exposure for camera {cam_id}...")
    
    # Let camera auto-adjust for a bit
    for i in range(stabilization_frames):
        ret, frame = cap.read()
        if not ret:
            print(f"⚠️ Failed to read frame during stabilization")
            return False
        time.sleep(0.033)  # ~30 fps
    
    # Read current exposure value
    current_exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
    
    # Switch to manual mode
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Manual mode
    
    # Set the exposure value we just measured
    if current_exposure != 0:
        cap.set(cv2.CAP_PROP_EXPOSURE, current_exposure)
    
    # Lock auto white balance too
    cap.set(cv2.CAP_PROP_AUTO_WB, 0)  # Disable auto white balance
    
    exposure_locked[cam_id] = True
    
    actual_exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
    print(f"✅ Exposure locked at {actual_exposure}")
    
    return True


def unlock_exposure(cam_id=0):
    """
    Unlock exposure to allow auto-adjustment.
    
    Args:
        cam_id: Camera ID to unlock
    """
    cap = caps.get(cam_id)
    if cap is None:
        return
    
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)  # Auto mode
    cap.set(cv2.CAP_PROP_AUTO_WB, 1)  # Enable auto white balance
    
    exposure_locked[cam_id] = False
    print(f"🔓 Exposure unlocked for camera {cam_id}")


def is_exposure_locked(cam_id=0):
    """Check if exposure is locked for a camera."""
    return exposure_locked.get(cam_id, False)


def optimize_camera_settings(cam_id=0):
    """
    Optimize camera settings for pellet detection.
    
    - Disable auto-focus if possible
    - Set appropriate brightness/contrast
    - Optimize for fast frame capture
    
    Args:
        cam_id: Camera ID to optimize
    """
    cap = caps.get(cam_id)
    if cap is None:
        return
    
    print(f"⚙️ Optimizing camera {cam_id} settings...")
    
    # Disable autofocus (keeps focus consistent)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    
    # Set focus to infinity or mid-range (adjust based on your setup)
    # You may need to tune this value (0-255 typical)
    cap.set(cv2.CAP_PROP_FOCUS, 0)
    
    # Reduce brightness slightly to avoid oversaturation on white target
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # 0-255, 128 = middle
    
    # Increase contrast to make pellet marks more visible
    cap.set(cv2.CAP_PROP_CONTRAST, 150)  # 0-255, higher = more contrast
    
    # Maximize frame rate
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Disable any image processing that might cause inconsistency
    cap.set(cv2.CAP_PROP_GAIN, 0)  # Disable automatic gain
    
    print(f"✅ Camera {cam_id} optimized")


def get_frame(cam_id=0):
    """
    Capture and process a frame from the specified camera.
    
    Args:
        cam_id: Camera ID to capture from
    
    Returns:
        Processed frame with overlays, or None if capture failed
    """
    cap = caps.get(cam_id)
    if cap is None:
        return None

    ret, frame = cap.read()
    if not ret:
        return None

    # Apply perspective warp if configured
    frame = warp(frame)
    
    # Process for detection
    return process_frame(frame, cam_id)


def get_camera_info(cam_id=0):
    """
    Get current camera settings and info.
    
    Args:
        cam_id: Camera ID
    
    Returns:
        Dictionary of camera properties
    """
    cap = caps.get(cam_id)
    if cap is None:
        return {}
    
    return {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": int(cap.get(cv2.CAP_PROP_FPS)),
        "exposure": cap.get(cv2.CAP_PROP_EXPOSURE),
        "auto_exposure": int(cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)),
        "brightness": int(cap.get(cv2.CAP_PROP_BRIGHTNESS)),
        "contrast": int(cap.get(cv2.CAP_PROP_CONTRAST)),
        "exposure_locked": exposure_locked.get(cam_id, False)
    }


def release_cameras():
    """Release all camera resources."""
    for cap in caps.values():
        cap.release()
    
    caps.clear()
    exposure_locked.clear()
    print("📷 All cameras released")
