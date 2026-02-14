from flask import Flask, render_template, Response, request, jsonify, send_file
from camera_manager import (
    init_cameras, get_frame, get_raw_frame, lock_exposure, unlock_exposure, 
    is_exposure_locked, optimize_camera_settings, get_camera_info,
    set_zoom, adjust_zoom, get_zoom,
    set_rotation, get_rotation,
    lock_white_balance, unlock_white_balance, set_white_balance
)
from calibration import set_calibration, get_calibration_quality
from scoring import set_scoring_config, get_scoring_config
from shot_recorder import (
    start_new_round, get_shot_image, stack_shots, unstack_shot,
    create_round_summary, get_round_statistics, list_rounds, load_round,
    delete_round, enable_recording
)
import json
import cv2
import threading
from heatmap import toggle_heatmap, reset_heatmap
import os
import subprocess
import re

# Load configuration
cfg = json.load(open("config.json"))

# Try to import detection module
try:
    from detection import toggle_detection, get_hits, reset_hits, get_round_summary
    DETECTION_AVAILABLE = True
except ImportError:
    print("⚠️ Detection module not available - creating stub")
    DETECTION_AVAILABLE = False
    
    # Create stub functions
    def toggle_detection():
        return False
    
    def get_hits():
        return []
    
    def reset_hits():
        pass
    
    def get_round_summary():
        return {"total": 0, "shots": []}

# Try to import breakbeam module
try:
    from breakbeam import watch_breakbeam, setup_gpio
    BREAKBEAM_AVAILABLE = True
except ImportError:
    print("⚠️ Breakbeam module not available")
    BREAKBEAM_AVAILABLE = False

# Start breakbeam monitoring thread if available
if BREAKBEAM_AVAILABLE:
    threading.Thread(
        target=watch_breakbeam,
        daemon=True
    ).start()

app = Flask(__name__)

# Initialize cameras
init_cameras(cfg["cameras"])

# Optimize camera settings if configured
if cfg.get("optimize_camera_on_start", True):
    for cam_id in cfg["cameras"]:
        optimize_camera_settings(cam_id)

# Auto-lock exposure if configured
if cfg.get("auto_lock_exposure", True):
    for cam_id in cfg["cameras"]:
        lock_exposure(cam_id, cfg.get("exposure_stabilization_frames", 30))


def check_v4l_utils():
    """Check if v4l-utils is installed."""
    try:
        subprocess.run(["v4l2-ctl", "--version"], capture_output=True)
        print("✅ v4l-utils is available")
        return True
    except FileNotFoundError:
        print("❌ v4l-utils not found. Install: sudo apt install v4l-utils")
        return False


def get_v4l2_device(cam_id):
    """Get V4L2 device path for camera ID."""
    return f"/dev/video{cam_id}"


def get_v4l2_control_value(cam_id, control):
    """Get current value of a V4L2 control."""
    device = get_v4l2_device(cam_id)
    try:
        cmd = ["v4l2-ctl", "-d", device, "-C", control]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Parse: "brightness: 128"
            match = re.search(r':\s*(-?\d+)', result.stdout)
            if match:
                return int(match.group(1))
        return None
    except Exception as e:
        print(f"❌ Failed to get {control}: {e}")
        return None


def get_v4l2_control_info(cam_id, control):
    """Get min, max, default, and current value for a control."""
    device = get_v4l2_device(cam_id)
    try:
        cmd = ["v4l2-ctl", "-d", device, "-L"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if control in line:
                    # Parse: "brightness 0x00980900 (int) : min=-64 max=64 step=1 default=0 value=10"
                    match = re.search(r'min=(-?\d+)\s+max=(-?\d+).*default=(-?\d+)\s+value=(-?\d+)', line)
                    if match:
                        return {
                            "min": int(match.group(1)),
                            "max": int(match.group(2)),
                            "default": int(match.group(3)),
                            "value": int(match.group(4)),
                            "supported": True
                        }
        return {"supported": False}
    except Exception as e:
        print(f"❌ Failed to get info for {control}: {e}")
        return {"supported": False}


def set_v4l2_control(cam_id, control, value):
    """Set V4L2 control using v4l2-ctl with error handling."""
    device = get_v4l2_device(cam_id)
    try:
        cmd = ["v4l2-ctl", "-d", device, "-c", f"{control}={value}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            error_msg = result.stderr.strip()
            # Don't log permission denied for white_balance_temperature (common issue)
            if "Permission denied" in error_msg and "white_balance_temperature" in control:
                return False
            print(f"❌ V4L2 control failed: {control}: {error_msg}")
            return False
    except FileNotFoundError:
        print("❌ v4l2-ctl not found. Install: sudo apt install v4l-utils")
        return False
    except Exception as e:
        print(f"❌ V4L2 error: {e}")
        return False


def get_all_v4l2_controls(cam_id):
    """Get all available controls with their full info."""
    device = get_v4l2_device(cam_id)
    controls = {}
    try:
        cmd = ["v4l2-ctl", "-d", device, "-L"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                # Parse control lines
                match = re.match(r'\s*(\w+)\s+0x[0-9a-f]+\s+\((\w+)\)\s*:\s*min=(-?\d+)\s+max=(-?\d+).*default=(-?\d+)\s+value=(-?\d+)', line)
                if match:
                    name = match.group(1)
                    controls[name] = {
                        "min": int(match.group(3)),
                        "max": int(match.group(4)),
                        "default": int(match.group(5)),
                        "value": int(match.group(6)),
                        "type": match.group(2)
                    }
        return controls
    except Exception as e:
        print(f"❌ Failed to list controls: {e}")
        return {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video/<int:cam>")
def video(cam):
    """Stream video from specified camera with detection overlay."""
    def gen():
        while True:
            frame = get_frame(cam)
            if frame is None:
                continue
            _, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                   buffer.tobytes() + b"\r\n")
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/raw_video/<int:cam>")
def raw_video(cam):
    """Stream raw video (no detection overlay) from specified camera."""
    def gen():
        while True:
            frame = get_raw_frame(cam)
            if frame is None:
                continue
            _, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                   buffer.tobytes() + b"\r\n")
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/toggle")
def toggle():
    """Toggle shot detection on/off."""
    return {"active": toggle_detection()}


@app.route("/hits")
def hits():
    """Get all detected hits."""
    return jsonify(get_hits())


@app.route("/hits/<int:cam>")
def hits_for_camera(cam):
    """Get hits for specific camera/lane."""
    all_hits = get_hits()
    return jsonify(all_hits)


@app.route("/round_summary")
def round_summary():
    """Get current round summary with statistics."""
    return jsonify(get_round_summary())


@app.route("/spectator")
def spectator():
    """Multi-camera spectator view page."""
    cameras = cfg.get("cameras", [0])
    return render_template("spectator.html", cameras=cameras)


@app.route("/spectator_fullscreen")
def spectator_fullscreen():
    """Full-screen multi-camera spectator mode."""
    cameras = cfg.get("cameras", [0])
    return render_template("spectator_fullscreen.html", cameras=cameras)


@app.route("/reset")
def reset():
    """Clear all hits and start new round."""
    reset_hits()
    start_new_round()
    return "OK"


@app.route("/toggle_heatmap")
def toggle_heat():
    """Toggle heatmap visualization."""
    state = toggle_heatmap()
    return {"heatmap": state}


@app.route("/heatmap_status")
def heatmap_status():
    """Get heatmap status."""
    from heatmap import is_heatmap_enabled, get_heatmap
    heatmap_data = get_heatmap()
    has_data = heatmap_data is not None and heatmap_data.max() > 0
    return jsonify({
        "enabled": is_heatmap_enabled(),
        "has_data": has_data
    })


@app.route("/reset_heatmap")
def reset_heat():
    """Clear heatmap data."""
    reset_heatmap()
    return "OK"


@app.route("/set_calibration", methods=["POST"])
def set_cal():
    """Set calibration data from frontend."""
    data = request.json
    set_calibration(data)
    quality = get_calibration_quality(data.get("camera_id", 0))
    return {"status": "OK", "quality": quality}


@app.route("/calibrate")
def calibrate():
    """Calibration page."""
    cameras = cfg.get("cameras", [0])
    return render_template("calibrate.html", cameras=cameras)

@app.route("/video_cropped/<int:cam_id>")
def video_cropped(cam_id):
    """
    Stream cropped video centered on calibrated target rings.
    This provides a zoomed-in view of just the target area.
    """
    def gen():
        from calibration import get_target
        
        while True:
            frame = get_frame(cam_id)
            if frame is None:
                continue
            
            # Get calibration data
            target = get_target(cam_id)
            
            if target.get("center") and target.get("rings_px"):
                cx, cy = target["center"]
                
                # Calculate crop area: 120% of outer ring diameter
                outer_ring_radius = int(target["rings_px"][-1])  # Last ring
                crop_radius = int(outer_ring_radius * 1.2)
                
                # Ensure crop stays within frame bounds
                h, w = frame.shape[:2]
                x1 = max(0, cx - crop_radius)
                y1 = max(0, cy - crop_radius)
                x2 = min(w, cx + crop_radius)
                y2 = min(h, cy + crop_radius)
                
                # Crop frame
                frame = frame[y1:y2, x1:x2]
            
            # Apply overlay (target rings will be drawn relative to new crop)
            frame = draw_overlay(frame, cam_id)
            
            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ========== Camera Control Endpoints ==========

@app.route("/camera_urls")
def camera_urls():
    """Get list of camera URLs and lane names."""
    cameras = []
    lane_names = cfg.get("lane_names", {})
    
    for cam_id in cfg.get("cameras", [0]):
        cameras.append({
            "camera_id": cam_id,
            "video_url": f"/video/{cam_id}",
            "raw_url": f"/raw_video/{cam_id}",
            "lane": lane_names.get(str(cam_id), f"Lane {cam_id + 1}"),
            "display_num": cam_id + 1
        })
    
    return jsonify({"cameras": cameras})


@app.route("/camera_info/<int:cam_id>")
def camera_info(cam_id):
    """Get detailed camera information."""
    info = get_camera_info(cam_id)
    return jsonify(info)


@app.route("/set_zoom/<int:cam_id>/<float:zoom>")
def set_zoom_route(cam_id, zoom):
    """Set zoom level for camera."""
    actual_zoom = set_zoom(cam_id, zoom)
    return jsonify({"zoom": actual_zoom})


@app.route("/adjust_zoom/<int:cam_id>/<float:delta>")
def adjust_zoom_route(cam_id, delta):
    """Adjust zoom by delta."""
    new_zoom = adjust_zoom(cam_id, delta)
    return jsonify({"zoom": new_zoom})


@app.route("/get_zoom/<int:cam_id>")
def get_zoom_route(cam_id):
    """Get current zoom level."""
    zoom = get_zoom(cam_id)
    return jsonify({"zoom": zoom})


@app.route("/set_rotation/<int:cam_id>/<int:angle>")
def set_rotation_route(cam_id, angle):
    """Set rotation angle."""
    actual_angle = set_rotation(cam_id, angle)
    return jsonify({"rotation": actual_angle})


@app.route("/get_rotation/<int:cam_id>")
def get_rotation_route(cam_id):
    """Get current rotation."""
    rotation = get_rotation(cam_id)
    return jsonify({"rotation": rotation})


@app.route("/lock_exposure/<int:cam_id>")
def lock_exposure_route(cam_id):
    """Lock camera exposure."""
    success = lock_exposure(cam_id)
    return jsonify({"success": success, "locked": True})


@app.route("/unlock_exposure/<int:cam_id>")
def unlock_exposure_route(cam_id):
    """Unlock camera exposure."""
    unlock_exposure(cam_id)
    return jsonify({"success": True, "locked": False})


@app.route("/lock_white_balance/<int:cam_id>")
def lock_white_balance_route(cam_id):
    """Lock white balance."""
    success = lock_white_balance(cam_id)
    return jsonify({"success": success})


@app.route("/unlock_white_balance/<int:cam_id>")
def unlock_white_balance_route(cam_id):
    """Unlock white balance."""
    unlock_white_balance(cam_id)
    return jsonify({"success": True})


@app.route("/set_white_balance/<int:cam_id>/<int:temp>")
def set_white_balance_route(cam_id, temp):
    """Set white balance temperature."""
    actual = set_white_balance(cam_id, temp)
    return jsonify({"temperature": actual})


@app.route("/get_white_balance_status/<int:cam_id>")
def get_white_balance_status(cam_id):
    """Get white balance lock status."""
    from camera_manager import white_balance_locked
    locked = white_balance_locked.get(cam_id, False)
    
    # Try to get current temperature
    temp = None
    try:
        info = get_v4l2_control_info(cam_id, "white_balance_temperature")
        if info.get("supported"):
            temp = info.get("value")
    except:
        pass
    
    return jsonify({
        "locked": locked,
        "temperature": temp,
        "auto": not locked
    })


@app.route("/optimize_camera/<int:cam_id>")
def optimize_camera_route(cam_id):
    """Auto-optimize camera settings."""
    optimize_camera_settings(cam_id)
    return jsonify({"success": True})


# ========== V4L2 Camera Control Endpoints ==========

@app.route("/get_camera_controls/<int:cam_id>")
def get_camera_controls(cam_id):
    """Get all camera controls with proper defaults."""
    controls = {}
    
    # Define controls to fetch with safe defaults
    control_list = {
        "brightness": {"min": -64, "max": 64, "default": 0},
        "contrast": {"min": 0, "max": 64, "default": 32},
        "saturation": {"min": 0, "max": 128, "default": 64},
        "hue": {"min": -40, "max": 40, "default": 0},
        "white_balance_temperature_auto": {"min": 0, "max": 1, "default": 1},
        "gamma": {"min": 72, "max": 500, "default": 100},
        "gain": {"min": 0, "max": 255, "default": 0},
        "power_line_frequency": {"min": 0, "max": 2, "default": 2},
        "sharpness": {"min": 0, "max": 255, "default": 128},
        "backlight_compensation": {"min": 0, "max": 1, "default": 0},
        "exposure_auto": {"min": 0, "max": 3, "default": 3},
        "exposure_absolute": {"min": 1, "max": 5000, "default": 166},
        "focus_auto": {"min": 0, "max": 1, "default": 1},
        "focus_absolute": {"min": 0, "max": 255, "default": 0}
    }
    
    # Get actual values from camera
    for control, fallback in control_list.items():
        info = get_v4l2_control_info(cam_id, control)
        if info.get("supported"):
            controls[control] = info
        else:
            # Use fallback values if control not supported
            controls[control] = {
                "min": fallback["min"],
                "max": fallback["max"],
                "default": fallback["default"],
                "value": fallback["default"],
                "supported": False
            }
    
    return jsonify(controls)


@app.route("/set_brightness/<int:cam_id>/<int:value>")
def set_brightness(cam_id, value):
    """Set camera brightness."""
    success = set_v4l2_control(cam_id, "brightness", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_contrast/<int:cam_id>/<int:value>")
def set_contrast(cam_id, value):
    """Set camera contrast."""
    success = set_v4l2_control(cam_id, "contrast", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_saturation/<int:cam_id>/<int:value>")
def set_saturation(cam_id, value):
    """Set camera saturation."""
    success = set_v4l2_control(cam_id, "saturation", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_hue/<int:cam_id>/<int:value>")
def set_hue(cam_id, value):
    """Set camera hue."""
    success = set_v4l2_control(cam_id, "hue", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_gamma/<int:cam_id>/<int:value>")
def set_gamma(cam_id, value):
    """Set camera gamma."""
    success = set_v4l2_control(cam_id, "gamma", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_gain/<int:cam_id>/<int:value>")
def set_gain(cam_id, value):
    """Set camera gain (ISO)."""
    success = set_v4l2_control(cam_id, "gain", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_sharpness/<int:cam_id>/<int:value>")
def set_sharpness(cam_id, value):
    """Set camera sharpness."""
    success = set_v4l2_control(cam_id, "sharpness", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_backlight_compensation/<int:cam_id>/<int:value>")
def set_backlight_compensation(cam_id, value):
    """Set backlight compensation (0 or 1)."""
    success = set_v4l2_control(cam_id, "backlight_compensation", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_power_line_frequency/<int:cam_id>/<int:value>")
def set_power_line_frequency(cam_id, value):
    """Set power line frequency (0=Disabled, 1=50Hz, 2=60Hz)."""
    success = set_v4l2_control(cam_id, "power_line_frequency", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_exposure_auto/<int:cam_id>/<int:value>")
def set_exposure_auto(cam_id, value):
    """Set exposure auto mode (1=Manual, 3=Auto)."""
    success = set_v4l2_control(cam_id, "exposure_auto", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_exposure_absolute/<int:cam_id>/<int:value>")
def set_exposure_absolute(cam_id, value):
    """Set manual exposure value."""
    success = set_v4l2_control(cam_id, "exposure_absolute", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_focus_auto/<int:cam_id>/<int:value>")
def set_focus_auto(cam_id, value):
    """Set auto focus (0=Manual, 1=Auto)."""
    success = set_v4l2_control(cam_id, "focus_auto", value)
    return jsonify({"success": success, "value": value})


@app.route("/set_focus/<int:cam_id>/<int:value>")
def set_focus(cam_id, value):
    """Set manual focus value."""
    success = set_v4l2_control(cam_id, "focus_absolute", value)
    return jsonify({"success": success, "value": value})


@app.route("/reset_camera_controls/<int:cam_id>")
def reset_camera_controls(cam_id):
    """Reset all camera controls to their factory defaults."""
    try:
        controls = get_all_v4l2_controls(cam_id)
        success_count = 0
        
        for control_name, control_info in controls.items():
            default_value = control_info.get("default")
            if default_value is not None:
                if set_v4l2_control(cam_id, control_name, default_value):
                    success_count += 1
        
        return jsonify({
            "success": True,
            "message": f"Reset {success_count} controls to defaults",
            "count": success_count
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to reset: {str(e)}"
        })


# ========== Lane Name Management ==========

@app.route("/get_lane_names")
def get_lane_names():
    """Get custom lane names."""
    lane_names = cfg.get("lane_names", {})
    return jsonify(lane_names)


@app.route("/set_lane_name", methods=["POST"])
def set_lane_name():
    """Set custom lane name for a camera."""
    try:
        data = request.json
        cam_id = str(data.get("camera_id", 0))
        name = data.get("name", f"Lane {int(cam_id) + 1}")
        
        if "lane_names" not in cfg:
            cfg["lane_names"] = {}
        
        cfg["lane_names"][cam_id] = name
        
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
        
        return jsonify({"success": True, "camera_id": cam_id, "name": name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ========== Detection FPS Control ==========

@app.route("/set_detection_fps/<int:fps>")
def set_detection_fps(fps):
    """Set detection framerate."""
    try:
        cfg["detection_fps"] = fps
        with open('config.json', 'w') as f:
            json.dump(cfg, f, indent=2)
        return jsonify({"fps": fps})
    except:
        return jsonify({"fps": 5})


# ========== Scoring Configuration Endpoints ==========

@app.route("/set_scoring_config", methods=["POST"])
def set_scoring():
    """Set scoring configuration."""
    data = request.json
    
    # Update scoring config
    config = set_scoring_config(
        use_4_ring=data.get("use_4_ring"),
        enable_bull_hole_bonus=data.get("enable_bull_hole_bonus")
    )
    
    # Also update shots_per_round in main config
    if "shots_per_round" in data:
        cfg["shots_per_round"] = data["shots_per_round"]
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
    
    return jsonify(config)


@app.route("/get_scoring_config")
def get_scoring():
    """Get current scoring configuration."""
    config = get_scoring_config()
    config["shots_per_round"] = cfg.get("shots_per_round", 6)
    return jsonify(config)


# ========== Shot Recording Endpoints ==========

@app.route("/recording_stats")
def recording_stats():
    """Get shot recording statistics."""
    stats = get_round_statistics()
    return jsonify(stats)


@app.route("/get_shot_image/<int:shot_num>")
def get_shot(shot_num):
    """Get image for specific shot number."""
    image, metadata = get_shot_image(shot_num)
    
    if image is None:
        return {"error": "Shot not found"}, 404
    
    _, buffer = cv2.imencode(".jpg", image)
    return Response(buffer.tobytes(), mimetype="image/jpeg")


@app.route("/list_rounds")
def list_rounds_endpoint():
    """List all recorded rounds."""
    rounds = list_rounds()
    return jsonify({"rounds": rounds})


# ========== Settings & Pages ==========

@app.route("/settings")
def settings():
    """Settings configuration page."""
    return render_template("settings.html")


@app.route("/rounds")
def rounds():
    """Rounds viewer page."""
    return render_template("rounds.html")


@app.route("/camera")
def camera_page():
    return render_template("camera.html")


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/get_config")
def get_config():
    """Get complete system configuration."""
    with open('config.json', 'r') as f:
        config = json.load(f)
    return jsonify(config)


@app.route("/set_recording_config", methods=["POST"])
def set_recording_config():
    """Update recording settings."""
    try:
        data = request.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['record_shots'] = data.get('record_shots', True)
        config['record_full_frame'] = data.get('record_full_frame', False)
        config['crop_size'] = data.get('crop_size', 200)
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/set_shot_directory", methods=["POST"])
def set_shot_directory():
    """Set shot recording directory."""
    try:
        data = request.json
        directory = data.get('directory', '')
        os.makedirs(directory, exist_ok=True)
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        config['shot_directory'] = directory
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True, "directory": directory})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/set_advanced_config", methods=["POST"])
def set_advanced_config():
    """Update advanced detection settings."""
    try:
        data = request.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['adaptive_threshold'] = data.get('adaptive_threshold', True)
        config['color_detection'] = data.get('color_detection', True)
        config['min_confidence'] = data.get('min_confidence', 0.6)
        config['shot_cooldown_frames'] = data.get('shot_cooldown_frames', 9)
        config['min_area'] = data.get('min_area', 40)
        config['max_area'] = data.get('max_area', 400)
        config['max_shot_interval_seconds'] = data.get('max_shot_interval_seconds', 120)
        config['baseline_update_mode'] = data.get('baseline_update_mode', 'selective')
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/set_zoom_config", methods=["POST"])
def set_zoom_config():
    """Update zoom configuration."""
    try:
        data = request.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['min_zoom'] = data.get('min_zoom', 1.0)
        config['max_zoom'] = data.get('max_zoom', 4.0)
        config['zoom_step'] = data.get('zoom_step', 0.1)
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    # Initialize break-beam GPIO if available
    if BREAKBEAM_AVAILABLE:
        try:
            setup_gpio()
            threading.Thread(target=watch_breakbeam, daemon=True).start()
        except Exception as e:
            print(f"⚠️ Break-beam not available: {e}")
    
    check_v4l_utils()
    
    # Run Flask server
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True,
        use_reloader=False  # CRITICAL: Prevents camera access conflicts
    )
