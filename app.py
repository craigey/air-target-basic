from flask import Flask, render_template, Response, request, jsonify
from camera_manager import init_cameras, get_frame
from calibration import set_calibration
from detection import toggle_detection, get_hits, reset_hits
import json
import cv2
import threading
from breakbeam import watch_breakbeam
from heatmap import toggle_heatmap, reset_heatmap

threading.Thread(
    target=watch_breakbeam,
    daemon=True
).start()

cfg = json.load(open("config.json"))

app = Flask(__name__)
init_cameras(cfg["cameras"])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video/<int:cam>")
def video(cam):
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
    return {"active": toggle_detection()}

@app.route("/hits")
def hits():
    return jsonify(get_hits())
    
@app.route("/spectator")
def spectator():
    return render_template("spectator.html")

@app.route("/reset")
def reset():
    reset_hits()
    return "OK"

@app.route("/toggle_heatmap")
def toggle_heat():
    state = toggle_heatmap()
    return {"heatmap": state}

@app.route("/reset_heatmap")
def reset_heat():
    reset_heatmap()
    return "OK"

@app.route("/set_calibration", methods=["POST"])
def set_cal():
    data = request.json
    set_calibration(data)
    return "OK"
    
@app.route("/calibrate")
def calibrate():
    return render_template("calibrate.html")    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

setup_gpio()

threading.Thread(
    target=watch_breakbeam,
    daemon=True
).start()