from itertools import combinations
import numpy as np
# https://scikit-learn.org/stable/modules/metrics.html
# https://math.stackexchange.com/questions/1399401/measuring-rotation-and-translation-differences-between-two-matrices

# (sx, sy, ex, ey)
def estimate_diff(diff_list: list):
    mat_list = []
    for d1, d2, d3 in combinations(diff_list, 3):
        x1, y1, x1_, y1_ = d1
        x2, y2, x2_, y2_ = d2
        x3, y3, x3_, y3_ = d3

        left = np.array([
            [x1, y1, 1.],
            [x2, y2, 1.],
            [x3, y3, 1.]
        ])
        right = np.array([x1_, x2_, x3_])
        r1 = np.linalg.solve(left, right)

        right = np.array([y1_, y2_, y3_])
        r2 = np.linalg.solve(left, right)

        mat = np.vstack((r1, r2, np.array([0., 0., 1.])))
        mat_list.append(mat)
    
    # compare mat
    # find nearest mat group
    # return avg of mat group
