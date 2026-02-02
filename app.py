from flask import Flask, render_template, Response, request, jsonify
from camera_manager import (
    init_cameras, get_frame, lock_exposure, unlock_exposure, 
    is_exposure_locked, optimize_camera_settings, get_camera_info
)
from calibration import set_calibration, get_calibration_quality
from detection import toggle_detection, get_hits, reset_hits
import json
import cv2
import threading
from breakbeam import watch_breakbeam
from heatmap import toggle_heatmap, reset_heatmap

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


@app.route("/spectator")
def spectator():
    """Spectator view page."""
    return render_template("spectator.html")


@app.route("/reset")
def reset():
    """Clear all hits."""
    reset_hits()
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
