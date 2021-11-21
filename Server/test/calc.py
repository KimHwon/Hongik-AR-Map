from itertools import combinations
import random
import numpy as np
from numpy.core.numeric import Inf
from numpy.lib.function_base import diff
# https://scikit-learn.org/stable/modules/metrics.html
# https://math.stackexchange.com/questions/1399401/measuring-rotation-and-translation-differences-between-two-matrices


# (sx, sy, ex, ey)
def estimate_diff(diff_list: list):
    N = len(diff_list)

    leftx = np.zeros((N,3))
    rightx = np.zeros(N)
    lefty = np.zeros((N,3))
    righty = np.zeros(N)

    i = 0
    for sx, sy, ex, ey in diff_list:
        leftx[i] = [sx, sy, 1.]
        rightx[i] = ex
        lefty[i] = [sx, sy, 1.]
        righty[i] = ey
        i += 1
    
    try:
        r1, re1, _, _ = np.linalg.lstsq(leftx, rightx)  # x, residuals, rank, singular
        r2, re2, _, _ = np.linalg.lstsq(lefty, righty)
        
    except np.linalg.LinAlgError:
        print('LinAlgError')
        r1 = np.array([1., 0., 0.])
        r2 = np.array([0., 1., 0.])
        re1 = re2 = [np.Infinity]
    
    return np.array([
        r1,
        r2,
        np.array([0., 0., 1.])
    ]), re1[0], re2[0]

def decompose_transform(mat: np.ndarray):
    trans = mat[:,2][:2]
    scale = np.array([
        np.linalg.norm(mat[:,0][:2]),
        np.linalg.norm(mat[:,1][:2])
    ])
    rotate = np.stack([
        mat[:,0] / scale[0],
        mat[:,1] / scale[1],
        np.array([0., 0., 1.])
    ], axis=0).T
    return trans, scale, rotate