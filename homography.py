import cv2
import numpy as np

H = None

def set_homography(src_pts, dst_size=(800,800)):
    global H
    dst_pts = np.array([
        [0,0],
        [dst_size[0],0],
        [dst_size[0],dst_size[1]],
        [0,dst_size[1]]
    ], dtype=np.float32)

    H = cv2.getPerspectiveTransform(
        np.array(src_pts, dtype=np.float32),
        dst_pts
    )

def warp(frame):
    if H is None:
        return frame
    return cv2.warpPerspective(frame, H, (800,800))