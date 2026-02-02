from flask import Flask, render_template, Response, request, jsonify, send_file
from camera_manager import (
    init_cameras, get_frame, get_raw_frame, lock_exposure, unlock_exposure, 
    is_exposure_locked, optimize_camera_settings, get_camera_info,
    set_zoom, adjust_zoom, get_zoom
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
    """Stream video from specified camera."""
    def gen():
        while True:
            frame = get_frame(cam)
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


@app.route("/round_summary")
def round_summary():
    """Get current round summary with statistics."""
    return jsonify(get_round_summary())


@app.route("/spectator")
def spectator():
    """Spectator view page."""
    return render_template("spectator.html")


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
    return render_template("calibrate.html")


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


@app.route("/set_zoom/<int:cam>/<float:zoom>")
def set_camera_zoom(cam, zoom):
    """Set camera zoom level."""
    actual_zoom = set_zoom(cam, zoom)
    return {"camera": cam, "zoom": actual_zoom}


@app.route("/adjust_zoom/<int:cam>/<float:delta>")
def adjust_camera_zoom(cam, delta):
    """Adjust camera zoom by delta."""
    new_zoom = adjust_zoom(cam, delta)
    return {"camera": cam, "zoom": new_zoom}


@app.route("/get_zoom/<int:cam>")
def get_camera_zoom(cam):
    """Get current camera zoom level."""
    zoom = get_zoom(cam)
    return {"camera": cam, "zoom": zoom}


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
    
    # Encode image as JPEG
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
    
    # Return metadata only (images accessed via get_shot_image)
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


# ========== Settings Page ==========

@app.route("/settings")
def settings():
    """Settings configuration page."""
    return render_template("settings.html")


@app.route("/rounds")
def rounds():
    """Rounds viewer page."""
    return render_template("rounds.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
