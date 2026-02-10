from flask import Flask, render_template, Response, request, jsonify, send_file
from camera_manager import (
    init_cameras, get_frame, get_raw_frame, lock_exposure, unlock_exposure, 
    is_exposure_locked, optimize_camera_settings, get_camera_info,
    set_zoom, adjust_zoom, get_zoom,
    set_rotation, get_rotation,
    lock_white_balance, unlock_white_balance, set_white_balance
)
from calibration import set_calibration, get_calibration_quality
from detection import toggle_detection, get_hits, reset_hits, get_round_summary
from scoring import set_scoring_config, get_scoring_config
from shot_recorder import (
    start_new_round, get_shot_image, stack_shots, unstack_shot,
    create_round_summary, get_round_statistics, list_rounds, load_round,
    delete_round, enable_recording
)
import json
import cv2
import threading
from breakbeam import watch_breakbeam
from heatmap import toggle_heatmap, reset_heatmap
import os
import subprocess
import re

# Load configuration
cfg = json.load(open("config.json"))

# Start breakbeam monitoring thread
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


def get_v4l2_device(cam_id):
    """Get V4L2 device path for camera ID."""
    return f"/dev/video{cam_id}"

def set_v4l2_control(cam_id, control, value):
    """Set V4L2 control using v4l2-ctl."""
    device = get_v4l2_device(cam_id)
    try:
        cmd = ["v4l2-ctl", "-d", device, "-c", f"{control}={value}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"❌ V4L2 control failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ v4l2-ctl not found. Install with: sudo apt install v4l-utils")
        return False
    except Exception as e:
        print(f"❌ V4L2 error: {e}")
        return False

def get_v4l2_control(cam_id, control):
    """Get V4L2 control value."""
    device = get_v4l2_device(cam_id)
    try:
        cmd = ["v4l2-ctl", "-d", device, "-C", control]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Parse output: "brightness: 128"
            match = re.search(r':\s*(-?\d+)', result.stdout)
            if match:
                return int(match.group(1))
        return None
    except Exception as e:
        print(f"❌ V4L2 get error: {e}")
        return None

def get_all_v4l2_controls(cam_id):
    """Get all available V4L2 controls and their values."""
    device = get_v4l2_device(cam_id)
    controls = {}
    try:
        # List all controls
        cmd = ["v4l2-ctl", "-d", device, "-L"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Parse controls and their ranges
            for line in result.stdout.split('\n'):
                # Example: "brightness 0x00980900 (int)    : min=-64 max=64 step=1 default=0 value=0"
                match = re.match(r'\s*(\w+)\s+0x[0-9a-f]+\s+\((\w+)\)\s*:\s*min=(-?\d+)\s+max=(-?\d+).*value=(-?\d+)', line)
                if match:
                    name = match.group(1)
                    min_val = int(match.group(3))
                    max_val = int(match.group(4))
                    current = int(match.group(5))
                    controls[name] = {
                        "min": min_val,
                        "max": max_val,
                        "value": current
                    }
        return controls
    except Exception as e:
        print(f"❌ V4L2 list error: {e}")
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
    # Filter by camera if tracking camera_id in hit data
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
    quality = get_calibration_quality()
    return {"status": "OK", "quality": quality}


@app.route("/calibrate")
def calibrate():
    """Calibration page."""
    cameras = cfg.get("cameras", [0])
    return render_template("calibrate.html", cameras=cameras)


@app.route("/calibrate/<int:cam>")
def calibrate_camera(cam):
    """Calibration page for specific camera."""
    return render_template("calibrate.html", cameras=[cam], selected_camera=cam)


# ========== Camera Info & URLs ==========

@app.route("/camera_urls")
def camera_urls():
    """Get list of all cameras with 1-based numbering for display."""
    cameras = []
    for cam_id in cfg.get("cameras", [0]):
        lane_name = get_lane_name(cam_id)
        cameras.append({
            "camera_id": cam_id,  # Internal 0-based
            "display_num": cam_id + 1,  # Display 1-based
            "lane": lane_name or f"Lane {cam_id + 1}"
        })
    return jsonify({"cameras": cameras})

@app.route("/get_lane_names")
def get_lane_names():
    """Get saved lane names."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return jsonify(config.get('lane_names', {}))
    except:
        return jsonify({})


@app.route("/set_lane_name", methods=["POST"])
def set_lane_name():
    """Save custom lane name for a camera."""
    try:
        data = request.json
        cam_id = str(data.get('camera_id'))
        name = data.get('name', '')
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        if 'lane_names' not in config:
            config['lane_names'] = {}
        
        config['lane_names'][cam_id] = name
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_lane_name(cam_id):
    """Get lane name for camera."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config.get('lane_names', {}).get(str(cam_id))
    except:
        return None


# ========== Camera Control Endpoints ==========

@app.route("/lock_exposure/<int:cam>")
def lock_exp(cam):
    """Lock camera exposure to current settings."""
    success = lock_exposure(cam)
    return {"locked": success, "camera": cam}


@app.route("/unlock_exposure/<int:cam>")
def unlock_exp(cam):
    """Unlock camera exposure (re-enable auto)."""
    unlock_exposure(cam)
    return {"locked": False, "camera": cam}


@app.route("/lock_white_balance/<int:cam>")
def lock_wb(cam):
    """Lock white balance."""
    success = lock_white_balance(cam)
    return {"locked": success, "camera": cam}


@app.route("/unlock_white_balance/<int:cam>")
def unlock_wb(cam):
    """Unlock white balance (re-enable auto)."""
    unlock_white_balance(cam)
    return {"locked": False, "camera": cam}


@app.route("/set_white_balance/<int:cam>/<int:temperature>")
def set_wb_temp(cam, temperature):
    """Set white balance temperature (2800-6500K)."""
    actual = set_white_balance(cam, temperature)
    return {"camera": cam, "temperature": actual}


@app.route("/camera_info/<int:cam>")
def camera_info(cam):
    """Get current camera settings and status."""
    info = get_camera_info(cam)
    return jsonify(info)


@app.route("/optimize_camera/<int:cam>")
def optimize_cam(cam):
    """Optimize camera settings for detection."""
    optimize_camera_settings(cam)
    return {"status": "OK", "camera": cam}


@app.route("/set_zoom/<int:cam>/<zoom>")
def set_zoom_route(cam, zoom):
    """Set zoom level (handles integers and floats)."""
    try:
        zoom_val = float(zoom)
        from camera_manager import set_zoom
        new_zoom = set_zoom(cam, zoom_val)
        print(f"🔍 Camera {cam} zoom set to {new_zoom}x")
        return jsonify({"zoom": new_zoom})
    except Exception as e:
        print(f"❌ Zoom set failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/adjust_zoom/<int:cam>/<delta>")
def adjust_zoom_route(cam, delta):
    """Adjust zoom by delta (handles negative values)."""
    try:
        delta_val = float(delta)
        from camera_manager import adjust_zoom
        new_zoom = adjust_zoom(cam, delta_val)
        print(f"🔍 Camera {cam} zoom adjusted by {delta_val} to {new_zoom}x")
        return jsonify({"zoom": new_zoom})
    except Exception as e:
        print(f"❌ Zoom adjustment failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_zoom/<int:cam>")
def get_camera_zoom(cam):
    """Get current camera zoom level."""
    zoom = get_zoom(cam)
    return {"camera": cam, "zoom": zoom}


@app.route("/set_rotation/<int:cam>/<int:angle>")
def set_camera_rotation(cam, angle):
    """Set camera rotation angle (0, 90, 180, 270, or any value)."""
    actual_angle = set_rotation(cam, angle)
    return {"camera": cam, "rotation": actual_angle}


@app.route("/get_rotation/<int:cam>")
def get_camera_rotation(cam):
    """Get current camera rotation angle."""
    angle = get_rotation(cam)
    return {"camera": cam, "rotation": angle}

@app.route("/set_brightness/<int:cam>/<int:value>")
def set_brightness_route(cam, value):
    """Set camera brightness (typically -64 to 64 for Logitech)."""
    try:
        success = set_v4l2_control(cam, "brightness", value)
        if success:
            return jsonify({"success": True, "brightness": value})
        else:
            return jsonify({"error": "Failed to set brightness"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_contrast/<int:cam>/<int:value>")
def set_contrast_route(cam, value):
    """Set camera contrast (typically 0 to 64 for Logitech)."""
    try:
        success = set_v4l2_control(cam, "contrast", value)
        if success:
            return jsonify({"success": True, "contrast": value})
        else:
            return jsonify({"error": "Failed to set contrast"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_saturation/<int:cam>/<int:value>")
def set_saturation_route(cam, value):
    """Set camera saturation (typically 0 to 128 for Logitech)."""
    try:
        success = set_v4l2_control(cam, "saturation", value)
        if success:
            return jsonify({"success": True, "saturation": value})
        else:
            return jsonify({"error": "Failed to set saturation"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_sharpness/<int:cam>/<int:value>")
def set_sharpness_route(cam, value):
    """Set camera sharpness (typically 0 to 255 for Logitech)."""
    try:
        success = set_v4l2_control(cam, "sharpness", value)
        if success:
            return jsonify({"success": True, "sharpness": value})
        else:
            return jsonify({"error": "Failed to set sharpness"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_gain/<int:cam>/<int:value>")
def set_gain_route(cam, value):
    """Set camera gain (ISO sensitivity)."""
    try:
        success = set_v4l2_control(cam, "gain", value)
        if success:
            return jsonify({"success": True, "gain": value})
        else:
            return jsonify({"error": "Failed to set gain"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/set_focus/<int:cam>/<int:value>")
def set_focus_route(cam, value):
    """Set camera focus (if manual focus supported)."""
    try:
        # Disable auto-focus first
        set_v4l2_control(cam, "focus_auto", 0)
        success = set_v4l2_control(cam, "focus_absolute", value)
        if success:
            return jsonify({"success": True, "focus": value})
        else:
            return jsonify({"error": "Failed to set focus"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_focus_auto/<int:cam>/<int:enabled>")
def set_focus_auto_route(cam, enabled):
    """Enable/disable auto-focus."""
    try:
        success = set_v4l2_control(cam, "focus_auto", enabled)
        if success:
            return jsonify({"success": True, "focus_auto": enabled})
        else:
            return jsonify({"error": "Failed to set auto-focus"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_backlight_compensation/<int:cam>/<int:value>")
def set_backlight_compensation_route(cam, value):
    """Set backlight compensation (0 or 1)."""
    try:
        success = set_v4l2_control(cam, "backlight_compensation", value)
        if success:
            return jsonify({"success": True, "backlight_compensation": value})
        else:
            return jsonify({"error": "Failed to set backlight compensation"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_power_line_frequency/<int:cam>/<int:value>")
def set_power_line_frequency_route(cam, value):
    """Set power line frequency (0=disabled, 1=50Hz, 2=60Hz)."""
    try:
        success = set_v4l2_control(cam, "power_line_frequency", value)
        if success:
            return jsonify({"success": True, "power_line_frequency": value})
        else:
            return jsonify({"error": "Failed to set power line frequency"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reset_camera_controls/<int:cam>")
def reset_camera_controls_route(cam):
    """Reset all camera controls to defaults."""
    try:
        device = get_v4l2_device(cam)
        cmd = ["v4l2-ctl", "-d", device, "--set-ctrl=reset_all_controls=1"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Also try individual resets
        set_v4l2_control(cam, "brightness", 0)
        set_v4l2_control(cam, "contrast", 32)
        set_v4l2_control(cam, "saturation", 64)
        set_v4l2_control(cam, "sharpness", 128)
        set_v4l2_control(cam, "gain", 0)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== UTILITY: Install v4l-utils if needed ==========
def check_v4l_utils():
    """Check if v4l-utils is installed."""
    try:
        subprocess.run(["v4l2-ctl", "--version"], capture_output=True)
        print("✓ v4l-utils installed")
        return True
    except FileNotFoundError:
        print("⚠️  v4l-utils not found")
        print("   Install with: sudo apt install v4l-utils")
        return False


@app.route("/get_camera_controls/<int:cam>")
def get_camera_controls_route(cam):
    """Get all camera control values using V4L2."""
    try:
        controls = get_all_v4l2_controls(cam)
        return jsonify(controls)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/heatmap_status")
def heatmap_status():
    """Get heatmap status."""
    try:
        from heatmap import is_heatmap_enabled, get_heatmap_normalized
        enabled = is_heatmap_enabled()
        has_data = len(get_heatmap_normalized()) > 0 if enabled else False
        return jsonify({
            "enabled": enabled,
            "has_data": has_data
        })
    except Exception as e:
        return jsonify({"enabled": False, "has_data": False})


@app.route("/set_detection_fps/<int:fps>")
def set_detection_fps(fps):
    """Set detection framerate."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['detection_fps'] = fps
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True, "fps": fps})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_detection_fps")
def get_detection_fps():
    """Get current detection framerate."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return jsonify({"fps": config.get('detection_fps', 5)})
    except:
        return jsonify({"fps": 5})


# ========== Scoring Configuration Endpoints ==========

@app.route("/set_scoring_config", methods=["POST"])
def set_scoring():
    """
    Set scoring configuration (4-ring vs 3-ring, bull hole bonus).
    
    POST data:
    {
        "use_4_ring": true/false,
        "enable_bull_hole_bonus": true/false
    }
    """
    data = request.json
    config = set_scoring_config(
        use_4_ring=data.get("use_4_ring"),
        enable_bull_hole_bonus=data.get("enable_bull_hole_bonus")
    )
    return jsonify(config)


@app.route("/get_scoring_config")
def get_scoring():
    """Get current scoring configuration."""
    config = get_scoring_config()
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


@app.route("/get_shot_metadata/<int:shot_num>")
def get_shot_meta(shot_num):
    """Get metadata for specific shot."""
    _, metadata = get_shot_image(shot_num)
    
    if metadata is None:
        return {"error": "Shot not found"}, 404
    
    return jsonify(metadata)


@app.route("/stack_shots")
def stack_shots_endpoint():
    """Get stacked composite of all shots."""
    composite = stack_shots()
    
    if composite is None:
        return {"error": "No shots to stack"}, 404
    
    _, buffer = cv2.imencode(".jpg", composite)
    return Response(buffer.tobytes(), mimetype="image/jpeg")


@app.route("/stack_shots/<int:up_to>")
def stack_shots_up_to(up_to):
    """Get stacked composite up to specific shot."""
    composite = stack_shots(up_to_shot=up_to)
    
    if composite is None:
        return {"error": "No shots to stack"}, 404
    
    _, buffer = cv2.imencode(".jpg", composite)
    return Response(buffer.tobytes(), mimetype="image/jpeg")


@app.route("/unstack_shot/<int:shot_num>")
def unstack_shot_endpoint(shot_num):
    """Get target state before specific shot."""
    composite = unstack_shot(shot_num)
    
    if composite is None:
        return {"error": "Cannot unstack"}, 404
    
    _, buffer = cv2.imencode(".jpg", composite)
    return Response(buffer.tobytes(), mimetype="image/jpeg")


@app.route("/round_summary_image")
def round_summary_image():
    """Get summary image for current round."""
    summary_path = create_round_summary()
    
    if summary_path is None or not os.path.exists(summary_path):
        return {"error": "No round summary available"}, 404
    
    return send_file(summary_path, mimetype="image/jpeg")


@app.route("/list_rounds")
def list_rounds_endpoint():
    """List all recorded rounds."""
    rounds = list_rounds()
    return jsonify({"rounds": rounds})


@app.route("/load_round/<round_dir>")
def load_round_endpoint(round_dir):
    """Load a previously recorded round."""
    shots = load_round(round_dir)
    
    if not shots:
        return {"error": "Round not found or empty"}, 404
    
    metadata_list = [meta for _, meta in shots]
    return jsonify({"round": round_dir, "shots": metadata_list})


@app.route("/delete_round/<round_dir>", methods=["DELETE"])
def delete_round_endpoint(round_dir):
    """Delete a recorded round."""
    delete_round(round_dir)
    return {"status": "OK", "deleted": round_dir}


@app.route("/enable_recording/<int:enabled>")
def enable_recording_endpoint(enabled):
    """Enable or disable shot recording."""
    enable_recording(enabled == 1)
    return {"recording": enabled == 1}


# ========== Settings & Scoring Pages ==========

@app.route("/settings")
def settings():
    """Settings configuration page."""
    cameras = cfg.get("cameras", [0])
    return render_template("settings.html", cameras=cameras)


@app.route("/rounds")
def rounds():
    """Rounds viewer page."""
    return render_template("rounds.html")


@app.route("/scoring")
def scoring():
    """Full scoring interface (external HTML)."""
    return render_template("scoring.html")

@app.route("/camera")
def camera_page():
    return render_template("camera.html")

@app.route("/help")
def help_page():
    return render_template("help.html")

@app.route("/get_config")
def get_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return jsonify(config)

@app.route("/set_recording_config", methods=["POST"])
def set_recording_config():
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
    try:
        data = request.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['adaptive_threshold'] = data.get('adaptive_threshold', True)
        config['color_detection'] = data.get('color_detection', True)
        config['min_confidence'] = data.get('min_confidence', 0.6)
        config['shot_cooldown_frames'] = data.get('shot_cooldown_frames', 9)
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    # Initialize break-beam GPIO if available
    try:
        from breakbeam import setup_gpio, watch_breakbeam
        import threading
        
        setup_gpio()
        threading.Thread(target=watch_breakbeam, daemon=True).start()
    except Exception as e:
        print(f"⚠️ Break-beam not available: {e}")
    check_v4l_utils()
    
    # Run Flask server
    # IMPORTANT: use_reloader=False prevents camera re-initialization errors
    # For HTTPS, uncomment and provide certificate paths:
    #app.run(
    #     host="0.0.0.0",
    #     port=5000,
    #     ssl_context=('/home/admin/air-target-basic-main/certs/raspberrypi.crt', '/home/admin/air-target-basic-main/certs/raspberrypi.key'),
    #     debug=True,
    #     use_reloader=False
    # )

    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True,
        use_reloader=False  # CRITICAL: Prevents camera access conflicts
    )
