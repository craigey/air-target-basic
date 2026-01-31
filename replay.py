from collections import deque

buffer = deque(maxlen=30)  # ~1s at 30fps
shots = []

def add_frame(frame):
    buffer.append(frame.copy())

def register_shot():
    shots.append(list(buffer))

def get_shots():
    return shots