from itertools import combinations
import random
import numpy as np
from numpy.lib.function_base import diff
# https://scikit-learn.org/stable/modules/metrics.html
# https://math.stackexchange.com/questions/1399401/measuring-rotation-and-translation-differences-between-two-matrices

RANDOM_SELECT = 1000

# (sx, sy, ex, ey)
def estimate_diff(diff_list: list):
    elems_list = [[np.zeros(0) for _x in range(3)] for _y in range(2)]
    mat_list = []
    xs = []
    ys = []
    #mat_list = np.zeros(RANDOM_SELECT, dtype=np.ndarray)
    #for iter in range(RANDOM_SELECT):
    #    d1, d2, d3 = random.sample(diff_list, 3)
    for d1,d2,d3 in combinations(diff_list, 3):
        x1, y1, x1_, y1_ = d1
        x2, y2, x2_, y2_ = d2
        x3, y3, x3_, y3_ = d3

        left = np.array([
            [x1, y1, 1.],
            [x2, y2, 1.],
            [x3, y3, 1.]
        ])

        try:
            right = np.array([x1_, x2_, x3_])
            r1 = np.linalg.solve(left, right)
            '''
            for i in range(3):
                elems_list[0][i] = np.append(elems_list[0][i], r1[i])
            '''

            right = np.array([y1_, y2_, y3_])
            r2 = np.linalg.solve(left, right)
            '''
            for i in range(3):
                elems_list[1][i] = np.append(elems_list[1][i], r2[i])
            '''
        except np.linalg.LinAlgError:
            continue

        mat = np.array([
            r1, r2, [0., 0., 1.]
        ])
        #mat_list[iter] = mat
        mat_list.append(mat)
    '''
    max_std = 0.0
    for row in elems_list:
        for elems in row:
            max_std = max(max_std, np.std(elems))
    print(max_std)
    '''

    # compare mat
    # find nearest mat group
    # return avg of mat group


def estimate_diff2(diff_list: list):
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
        r1 = np.linalg.lstsq(leftx, rightx)
        r2 = np.linalg.lstsq(lefty, righty)
        return np.array([r1, r2, [0., 0., 1.]])
        
    except np.linalg.LinAlgError:
        print('LinAlgError')
        r1 = [1., 0., 0.]
        r2 = [0., 1., 0.]
    
    return np.array([r1, r2, [0., 0., 1.]])
    