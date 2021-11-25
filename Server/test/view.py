
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from itertools import product, combinations
import time

fig, ax, rot, tr = None, None, None, None

def init():
    global fig, ax, rot, tr

    plt.ion()

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.set_aspect('auto')

    rot = np.zeros((3,3))
    for i in range(3):
        rot[i][i] = 1
    tr = np.zeros(3)

def _rotate(point: np.ndarray, mat):
    vec = np.dot(mat, point)
    return vec.tolist()

def _trans(point, vec):
    return (point + vec).tolist()

def render(T = None, R = None):
    global fig, ax, rot, tr
    if fig is None:
        init()

    ax.clear()
    if not T is None:
        tr = T
    if not R is None:
        rot = R

    r = [-1, 1]
    for s, e in combinations(np.array(list(product(r, r, r))), 2):
        if np.sum(np.abs(s-e)) == r[1]-r[0]:

            s = _trans(s, tr)
            e = _trans(e, tr)

            s = _rotate(s, rot)
            e = _rotate(e, rot)
            
            ax.plot3D(*zip(s, e), color="b")
    
    fig.canvas.draw()
    fig.canvas.flush_events()

if __name__ == '__main__':
    init()
    while True:
        render()
        time.sleep(0.1)