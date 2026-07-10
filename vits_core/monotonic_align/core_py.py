"""
Pure Python/NumPy fallback for monotonic_align.core.maximum_path_c
Replaces the Cython extension when MSVC compiler is not available.
"""
import numpy as np


def maximum_path_c(paths, values, t_ys, t_xs):
    """Pure NumPy implementation of monotonic alignment search.
    
    Args:
        paths: np.ndarray[int32, shape=(B, T_y, T_x)] - output (filled with 0/1)
        values: np.ndarray[float32, shape=(B, T_y, T_x)] - input values
        t_ys: np.ndarray[int32, shape=(B,)] - valid lengths for dim y
        t_xs: np.ndarray[int32, shape=(B,)] - valid lengths for dim x
    """
    b = paths.shape[0]
    for i in range(b):
        maximum_path_each(paths[i], values[i], t_ys[i], t_xs[i])


def maximum_path_each(path, value, t_y, t_x, max_neg_val=-1e9):
    """Single-path monotonic alignment search.
    
    Args:
        path: np.ndarray[int32, shape=(T_y, T_x)] - output path matrix
        value: np.ndarray[float32, shape=(T_y, T_x)] - score matrix (modified in-place)
        t_y: int - valid length for text dimension
        t_x: int - valid length for spectrogram dimension
        max_neg_val: float - large negative value for invalid positions
    """
    # Forward pass: compute cumulative scores
    for y in range(t_y):
        x_start = max(0, t_x + y - t_y)
        x_end = min(t_x, y + 1)
        for x in range(x_start, x_end):
            if x == y:
                v_cur = max_neg_val
            else:
                v_cur = value[y - 1, x]
            
            if x == 0:
                if y == 0:
                    v_prev = 0.0
                else:
                    v_prev = max_neg_val
            else:
                v_prev = value[y - 1, x - 1]
            
            value[y, x] += max(v_prev, v_cur)
    
    # Backward pass: trace optimal path
    index = t_x - 1
    for y in range(t_y - 1, -1, -1):
        path[y, index] = 1
        if index != 0 and (index == y or value[y - 1, index] < value[y - 1, index - 1]):
            index = index - 1
