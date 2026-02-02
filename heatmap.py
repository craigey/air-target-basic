import numpy as np

# Heatmap data
heat = np.zeros((720, 1280), dtype=np.float32)

# Heatmap display toggle
_heatmap_enabled = False


def toggle_heatmap():
    global _heatmap_enabled
    _heatmap_enabled = not _heatmap_enabled
    return _heatmap_enabled


def is_heatmap_enabled():
    return _heatmap_enabled


def register_hit(x, y):
    ix, iy = int(x), int(y)
    if 0 <= iy < heat.shape[0] and 0 <= ix < heat.shape[1]:
        heat[iy, ix] += 1


def get_heatmap():
    return heat


def get_heatmap_normalized():
    h = heat.copy()
    if h.max() > 0:
        h = (h / h.max()) * 255
    return h.astype(np.uint8)


def reset_heatmap():
    heat[:] = 0