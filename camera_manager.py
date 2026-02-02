import cv2
from detection import process_frame
from homography import warp

caps = {}

def init_cameras(camera_ids=[0]):
    """
    Initialize USB cameras.
    camera_ids: list of integers (default [0])
    """
    global caps

    for cam_id in camera_ids:
        cap = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cap.isOpened():
            raise RuntimeError(f"❌ Cannot open camera {cam_id}")

        caps[cam_id] = cap

    print(f"✅ Initialized cameras: {list(caps.keys())}")

def get_frame(cam_id=0):
    cap = caps.get(cam_id)
    if cap is None:
        return None

    ret, frame = cap.read()
    if not ret:
        return None

    frame = warp(frame)
    return process_frame(frame, cam_id)

def release_cameras():
    for cap in caps.values():
        cap.release()