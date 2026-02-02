import cv2
import numpy as np
import time
from detection import process_frame
from homography import warp

caps = {}
exposure_locked = {}
zoom_levels = {}  # Track zoom level per camera

def init_cameras(camera_ids=[0]):
    """
    Initialize USB cameras with optimized settings.
    
    Args:
        camera_ids: list of camera IDs (default [0])
    """
    global caps, exposure_locked, zoom_levels

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
        zoom_levels[cam_id] = 1.0  # Default zoom
        
        print(f"✅ Initialized camera {cam_id}")

    print(f"✅ All cameras ready: {list(caps.keys())}")


def lock_exposure(cam_id=0, stabilization_frames=30):
    """
    Lock camera exposure to prevent auto-adjustment during shooting.
    
    Critical for consistent frame differencing!
    
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
    
    # Let camera auto-adjust
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


def set_zoom(cam_id=0, zoom_level=1.0):
    """
    Set digital zoom level for camera.
    
    Digital zoom crops and scales the image to focus on target area.
    Useful for narrowing down where the target is.
    
    Args:
        cam_id: Camera ID
        zoom_level: Zoom factor (1.0 = no zoom, 2.0 = 2x zoom, etc.)
    
    Returns:
        Actual zoom level set
    """
    import json
    cfg = json.load(open("config.json"))
    
    min_zoom = cfg.get("min_zoom", 1.0)
    max_zoom = cfg.get("max_zoom", 4.0)
    
    # Clamp zoom level
    zoom_level = max(min_zoom, min(max_zoom, zoom_level))
    
    zoom_levels[cam_id] = zoom_level
    
    print(f"🔍 Camera {cam_id} zoom set to {zoom_level:.1f}x")
    return zoom_level


def adjust_zoom(cam_id=0, delta=0.1):
    """
    Adjust zoom level by a delta amount.
    
    Args:
        cam_id: Camera ID
        delta: Amount to change zoom (positive = zoom in, negative = zoom out)
    
    Returns:
        New zoom level
    """
    current_zoom = zoom_levels.get(cam_id, 1.0)
    new_zoom = current_zoom + delta
    
    return set_zoom(cam_id, new_zoom)


def get_zoom(cam_id=0):
    """Get current zoom level for camera."""
    return zoom_levels.get(cam_id, 1.0)


def apply_digital_zoom(frame, zoom_level=1.0):
    """
    Apply digital zoom to a frame.
    
    Args:
        frame: Input frame
        zoom_level: Zoom factor
    
    Returns:
        Zoomed frame
    """
    if zoom_level <= 1.0:
        return frame
    
    h, w = frame.shape[:2]
    
    # Calculate crop dimensions
    crop_w = int(w / zoom_level)
    crop_h = int(h / zoom_level)
    
    # Center crop
    x1 = (w - crop_w) // 2
    y1 = (h - crop_h) // 2
    x2 = x1 + crop_w
    y2 = y1 + crop_h
    
    # Crop and scale back to original size
    cropped = frame[y1:y2, x1:x2]
    zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
    
    return zoomed


def optimize_camera_settings(cam_id=0):
    """
    Optimize camera settings for pellet detection.
    
    Args:
        cam_id: Camera ID to optimize
    """
    cap = caps.get(cam_id)
    if cap is None:
        return
    
    print(f"⚙️ Optimizing camera {cam_id} settings...")
    
    # Disable autofocus (keeps focus consistent)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    
    # Set focus to infinity or mid-range
    cap.set(cv2.CAP_PROP_FOCUS, 0)
    
    # Reduce brightness slightly to avoid oversaturation on white target
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # 0-255, 128 = middle
    
    # Increase contrast to make pellet marks more visible
    cap.set(cv2.CAP_PROP_CONTRAST, 150)  # 0-255, higher = more contrast
    
    # Maximize frame rate
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Disable automatic gain
    cap.set(cv2.CAP_PROP_GAIN, 0)
    
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

    # Apply digital zoom if set
    zoom = zoom_levels.get(cam_id, 1.0)
    if zoom > 1.0:
        frame = apply_digital_zoom(frame, zoom)
    
    # Apply perspective warp if configured
    frame = warp(frame)
    
    # Process for detection
    return process_frame(frame, cam_id)


def get_raw_frame(cam_id=0):
    """
    Get raw frame without processing (for calibration, etc.).
    
    Args:
        cam_id: Camera ID
    
    Returns:
        Raw frame with zoom applied
    """
    cap = caps.get(cam_id)
    if cap is None:
        return None

    ret, frame = cap.read()
    if not ret:
        return None

    # Apply digital zoom if set
    zoom = zoom_levels.get(cam_id, 1.0)
    if zoom > 1.0:
        frame = apply_digital_zoom(frame, zoom)
    
    return frame


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
        "exposure_locked": exposure_locked.get(cam_id, False),
        "zoom": zoom_levels.get(cam_id, 1.0)
    }


def release_cameras():
    """Release all camera resources."""
    for cap in caps.values():
        cap.release()
    
    caps.clear()
    exposure_locked.clear()
    zoom_levels.clear()
    print("📷 All cameras released")
