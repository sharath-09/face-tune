

from matplotlib import pyplot as plt
import numpy as np
from scipy.stats import linregress

def plot_y_axis_over_time(lmk_array: np.ndarray):
    """Plot y axis over time"""
    y_pos = lmk_array[:, 0, 1]
    time_axis = np.arange(y_pos.shape[0])
    plt.scatter(time_axis, y_pos)
    plt.show()

def plot_positions(lmk_array: np.ndarray):
    """Plot positions on axis"""
    x_pos = lmk_array[:, 0, 0]
    y_pos = lmk_array[:, 0, 1]
    plt.scatter(x_pos, y_pos)
    plt.show()

def get_slope(lmk_1: np.ndarray, lmk_2: np.ndarray):
    """Calculates slope between (x1,y1) and (x2,y2).

    Args:
        lmk_1: x1, y1)
        lmk_2: (x2, y2)
    """  
    print(lmk_1.shape)
    print(lmk_2.shape)
    
    # slope, _, _, _, _= linregress(lmk_1.tolist(), lmk_2.tolist())
    slope = lmk_1[-1] - lmk_2[-1]
    return slope