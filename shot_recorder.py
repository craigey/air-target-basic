import cv2
import numpy as np
import os
import json
from datetime import datetime
import shutil

cfg = json.load(open("config.json"))

# Shot recording state
_recording_enabled = cfg.get("record_shots", True)
_shots_dir = cfg.get("shot_images_dir", "/home/admin/air-target-basic-main/shots")
_current_round_dir = None
_shot_images = []  # List of (filepath, shot_data) tuples

def init_shot_recorder():
    """Initialize shot recorder and create directories."""
    global _shots_dir
    
    # Create base shots directory if it doesn't exist
    os.makedirs(_shots_dir, exist_ok=True)
    
    print(f"✅ Shot recorder initialized: {_shots_dir}")


def start_new_round():
    """
    Start a new round and create directory for this round's shots.
    
    Returns:
        Path to new round directory
    """
    global _current_round_dir, _shot_images
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _current_round_dir = os.path.join(_shots_dir, f"round_{timestamp}")
    
    os.makedirs(_current_round_dir, exist_ok=True)
    _shot_images = []
    
    print(f"📁 New round started: {_current_round_dir}")
    return _current_round_dir


def record_shot(frame, shot_data, shot_number):
    """
    Record a shot image with metadata.
    
    Args:
        frame: Full frame image (BGR)
        shot_data: Dictionary with shot information (score, x, y, etc.)
        shot_number: Shot number in current round
    
    Returns:
        Path to saved image
    """
    global _current_round_dir, _shot_images
    
    if not _recording_enabled:
        return None
    
    # Create round directory if not exists
    if _current_round_dir is None:
        start_new_round()
    
    # Determine what to save
    if cfg.get("record_full_frame", False):
        # Save full frame
        image_to_save = frame.copy()
    else:
        # Save cropped region around hit
        crop_size = cfg.get("record_crop_size", 200)
        x, y = int(shot_data["x"]), int(shot_data["y"])
        
        # Calculate crop bounds
        h, w = frame.shape[:2]
        x1 = max(0, x - crop_size // 2)
        y1 = max(0, y - crop_size // 2)
        x2 = min(w, x + crop_size // 2)
        y2 = min(h, y + crop_size // 2)
        
        # Crop and pad if necessary
        image_to_save = frame[y1:y2, x1:x2].copy()
        
        # Pad to square if needed
        if image_to_save.shape[0] != crop_size or image_to_save.shape[1] != crop_size:
            image_to_save = cv2.copyMakeBorder(
                image_to_save,
                0, crop_size - image_to_save.shape[0],
                0, crop_size - image_to_save.shape[1],
                cv2.BORDER_CONSTANT,
                value=[0, 0, 0]
            )
    
    # Create filename
    filename = f"shot_{shot_number:02d}_score_{shot_data['score']}.jpg"
    filepath = os.path.join(_current_round_dir, filename)
    
    # Save image
    cv2.imwrite(filepath, image_to_save, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    # Save metadata
    metadata = shot_data.copy()
    metadata["shot_number"] = shot_number
    metadata["timestamp"] = datetime.now().isoformat()
    metadata["filepath"] = filepath
    
    metadata_path = filepath.replace(".jpg", ".json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Track this shot
    _shot_images.append((filepath, metadata))
    
    print(f"📸 Shot {shot_number} recorded: {filename}")
    return filepath


def get_shot_image(shot_number):
    """
    Get image and metadata for a specific shot.
    
    Args:
        shot_number: Shot number (1-indexed)
    
    Returns:
        (image, metadata) tuple or (None, None) if not found
    """
    if shot_number < 1 or shot_number > len(_shot_images):
        return None, None
    
    filepath, metadata = _shot_images[shot_number - 1]
    
    if not os.path.exists(filepath):
        return None, None
    
    image = cv2.imread(filepath)
    return image, metadata


def stack_shots(up_to_shot=None):
    """
    Create a composite image showing all shots stacked on top of each other.
    This simulates the state of the target at any point during the round.
    
    Args:
        up_to_shot: Stack only up to this shot number (None = all shots)
    
    Returns:
        Stacked composite image
    """
    if not _shot_images:
        return None
    
    # Determine how many shots to stack
    if up_to_shot is None:
        shots_to_stack = _shot_images
    else:
        shots_to_stack = _shot_images[:up_to_shot]
    
    if not shots_to_stack:
        return None
    
    # Load first image as base
    base_path, _ = shots_to_stack[0]
    composite = cv2.imread(base_path).copy()
    
    # Stack remaining images using alpha blending
    for filepath, metadata in shots_to_stack[1:]:
        shot_img = cv2.imread(filepath)
        
        if shot_img.shape != composite.shape:
            shot_img = cv2.resize(shot_img, (composite.shape[1], composite.shape[0]))
        
        # Blend with existing composite (shows accumulation of marks)
        composite = cv2.addWeighted(composite, 0.7, shot_img, 0.3, 0)
    
    return composite


def unstack_shot(shot_number):
    """
    Show the target state BEFORE a specific shot (by stacking all previous shots).
    
    Args:
        shot_number: Shot to exclude (show target before this shot)
    
    Returns:
        Composite image of target before the specified shot
    """
    if shot_number <= 1:
        # Before shot 1, target is clean
        return get_clean_target_image()
    
    # Stack all shots up to but not including this one
    return stack_shots(up_to_shot=shot_number - 1)


def get_clean_target_image():
    """
    Get a clean target image (baseline before any shots).
    
    Returns:
        Clean target image or None
    """
    if _current_round_dir is None:
        return None
    
    baseline_path = os.path.join(_current_round_dir, "baseline.jpg")
    
    if os.path.exists(baseline_path):
        return cv2.imread(baseline_path)
    
    return None


def save_baseline(frame):
    """
    Save the baseline (clean target) image at start of round.
    
    Args:
        frame: Clean target frame
    """
    if _current_round_dir is None:
        start_new_round()
    
    baseline_path = os.path.join(_current_round_dir, "baseline.jpg")
    cv2.imwrite(baseline_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    print(f"📸 Baseline saved: {baseline_path}")


def create_round_summary():
    """
    Create a summary image showing all shots with annotations.
    
    Returns:
        Path to summary image
    """
    if not _shot_images or _current_round_dir is None:
        return None
    
    # Create grid layout
    num_shots = len(_shot_images)
    cols = min(3, num_shots)
    rows = (num_shots + cols - 1) // cols
    
    # Load first image to get dimensions
    first_img = cv2.imread(_shot_images[0][0])
    h, w = first_img.shape[:2]
    
    # Create canvas
    canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    
    # Place each shot
    for idx, (filepath, metadata) in enumerate(_shot_images):
        row = idx // cols
        col = idx % cols
        
        img = cv2.imread(filepath)
        if img.shape[:2] != (h, w):
            img = cv2.resize(img, (w, h))
        
        # Add text overlay
        score = metadata["score"]
        shot_num = metadata["shot_number"]
        
        text = f"#{shot_num}: {score}"
        cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   1.0, (0, 255, 0) if score >= 5 else (0, 0, 255), 2)
        
        # Place on canvas
        y1 = row * h
        x1 = col * w
        canvas[y1:y1+h, x1:x1+w] = img
    
    # Save summary
    summary_path = os.path.join(_current_round_dir, "round_summary.jpg")
    cv2.imwrite(summary_path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    print(f"📊 Round summary created: {summary_path}")
    return summary_path


def get_round_statistics():
    """
    Get statistics about current round recording.
    
    Returns:
        Dictionary with recording statistics
    """
    return {
        "recording_enabled": _recording_enabled,
        "current_round": _current_round_dir,
        "shots_recorded": len(_shot_images),
        "total_rounds": len([d for d in os.listdir(_shots_dir) 
                            if os.path.isdir(os.path.join(_shots_dir, d))]) if os.path.exists(_shots_dir) else 0
    }


def list_rounds():
    """
    List all recorded rounds.
    
    Returns:
        List of round directory names
    """
    if not os.path.exists(_shots_dir):
        return []
    
    rounds = [d for d in os.listdir(_shots_dir) 
             if os.path.isdir(os.path.join(_shots_dir, d)) and d.startswith("round_")]
    
    return sorted(rounds, reverse=True)  # Most recent first


def load_round(round_dir):
    """
    Load a previously recorded round.
    
    Args:
        round_dir: Round directory name
    
    Returns:
        List of (filepath, metadata) tuples
    """
    global _current_round_dir, _shot_images
    
    round_path = os.path.join(_shots_dir, round_dir)
    
    if not os.path.exists(round_path):
        return []
    
    _current_round_dir = round_path
    _shot_images = []
    
    # Load all shot metadata
    shot_files = sorted([f for f in os.listdir(round_path) 
                        if f.startswith("shot_") and f.endswith(".json")])
    
    for json_file in shot_files:
        json_path = os.path.join(round_path, json_file)
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        
        filepath = metadata["filepath"]
        _shot_images.append((filepath, metadata))
    
    print(f"📂 Loaded round: {round_dir} ({len(_shot_images)} shots)")
    return _shot_images


def delete_round(round_dir):
    """
    Delete a recorded round.
    
    Args:
        round_dir: Round directory name
    """
    round_path = os.path.join(_shots_dir, round_dir)
    
    if os.path.exists(round_path):
        shutil.rmtree(round_path)
        print(f"🗑️ Deleted round: {round_dir}")


def enable_recording(enabled=True):
    """Enable or disable shot recording."""
    global _recording_enabled
    _recording_enabled = enabled
    
    cfg["record_shots"] = enabled
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)
    
    print(f"📸 Recording {'enabled' if enabled else 'disabled'}")


def set_shots_directory(directory):
    """Update shots directory path."""
    global SHOTS_DIR, _current_round_dir
    SHOTS_DIR = directory
    _current_round_dir = None
    os.makedirs(SHOTS_DIR, exist_ok=True)
    print(f"✅ Shot directory updated: {SHOTS_DIR}")

# Initialize on import
init_shot_recorder()
