import numpy as np

heat = np.zeros((720,1280))

def register_hit(x,y):
    if y < heat.shape[0] and x < heat.shape[1]:
        heat[int(y)][int(x)] += 1

def get_heatmap():
    return heat
