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
    """
    Get camera stream URLs for all configured cameras.
    Used by external scoring systems.
    """
    base_url = request.host_url.rstrip('/')
    cameras = cfg.get("cameras", [0])
    
    urls = []
    for cam_id in cameras:
        urls.append({
            "camera_id": cam_id,
            "lane": cam_id + 1,
            "stream_url": f"{base_url}/video/{cam_id}",
            "raw_stream_url": f"{base_url}/raw_video/{cam_id}",
            "hits_url": f"{base_url}/hits/{cam_id}",
            "status_url": f"{base_url}/camera_info/{cam_id}"
        })
    
    return jsonify({
        "base_url": base_url,
        "cameras": urls,
        "total_cameras": len(urls)
    })


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


@app.route("/set_zoom/<int:cam>/<zoom>")  # Accept as string
def set_zoom_route(cam, zoom):
    try:
        zoom_val = float(zoom)  # Handles "2" and "2.0"
        new_zoom = set_zoom(cam, zoom_val)
        return jsonify({"zoom": new_zoom})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/adjust_zoom/<int:cam>/<delta>")  # Accept as string
def adjust_zoom_route(cam, delta):
    try:
        delta_val = float(delta)  # Parse string to float
        new_zoom = adjust_zoom(cam, delta_val)
        return jsonify({"zoom": new_zoom})
    except Exception as e:
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
    try:
        cap = get_camera(cam)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, value / 100.0)
        return jsonify({"success": True, "brightness": value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_contrast/<int:cam>/<int:value>")
def set_contrast_route(cam, value):
    try:
        cap = get_camera(cam)
        cap.set(cv2.CAP_PROP_CONTRAST, value / 100.0)
        return jsonify({"success": True, "contrast": value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_saturation/<int:cam>/<int:value>")
def set_saturation_route(cam, value):
    try:
        cap = get_camera(cam)
        cap.set(cv2.CAP_PROP_SATURATION, value / 100.0)
        return jsonify({"success": True, "saturation": value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_sharpness/<int:cam>/<int:value>")
def set_sharpness_route(cam, value):
    try:
        cap = get_camera(cam)
        cap.set(cv2.CAP_PROP_SHARPNESS, value / 100.0)
        return jsonify({"success": True, "sharpness": value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_camera_controls/<int:cam>")
def get_camera_controls_route(cam):
    try:
        cap = get_camera(cam)
        controls = {
            "brightness": int(cap.get(cv2.CAP_PROP_BRIGHTNESS) * 100),
            "contrast": int(cap.get(cv2.CAP_PROP_CONTRAST) * 100),
            "saturation": int(cap.get(cv2.CAP_PROP_SATURATION) * 100),
            "sharpness": int(cap.get(cv2.CAP_PROP_SHARPNESS) * 100)
        }
        return jsonify(controls)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    
    # Run Flask server
    # IMPORTANT: use_reloader=False prevents camera re-initialization errors
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True,
        use_reloader=False  # CRITICAL: Prevents camera access conflicts
    )
