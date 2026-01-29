import cv2
from detection import process_frame

cap = cv2.VideoCapture(0)

def stream_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        frame = process_frame(frame)

        _, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")
