import numpy as np

heat = np.zeros((720,1280))

def register_hit(x,y):
    if y < heat.shape[0] and x < heat.shape[1]:
        heat[int(y)][int(x)] += 1

def get_heatmap():
    return heat

def get_heatmap_normalized():
    h = heat.copy()
    if h.max() > 0:
        h = (h / h.max()) * 255
    return h.astype(np.uint8)

def reset_heatmap():
    global heat
    heat[:] = 0