
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
    x,y,z = vec
    vec = np.asarray([x[0], y[0], z[0]])
    return (point + vec).tolist()

def render(T: np.ndarray = None, R: np.ndarray = None, P: np.ndarray = None) -> None:
    global fig, ax, rot, tr
    if fig is None:
        init()

    ax.clear()

    N = np.array([0, 0, 1])
    if not R is None:
        rot = R
        N = _rotate(N, rot)

    if not T is None:
        tr = T
        N = _trans(N, tr)

    if not P is None:
        N = P

    ax.quiver(0, 0, 0, *N)

    ax.set_xlim([-100, 100])
    ax.set_ylim([-100, 100])
    ax.set_zlim([-100, 100])
    
    fig.canvas.draw()
    fig.canvas.flush_events()

if __name__ == '__main__':
    init()
    while True:
        render()
        time.sleep(0.1)