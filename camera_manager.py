from overlay import draw_overlay

def get_frame(cam_id):
    cap = caps.get(cam_id)
    success, frame = cap.read()

    if not success:
        return None

    return process_frame(frame, cam_id)
