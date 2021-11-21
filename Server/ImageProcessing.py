import traceback
import numpy as np
import io
from PIL import Image, ImageFile
import cv2

import traceback
from typing import *

from .Config import *
from .Logger import get_logger

Mat = np.ndarray

class ExceptionWrapper:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)
        except:
            logger.error(traceback.format_exc())
        return None


logger = get_logger(__name__)
ImageFile.LOAD_TRUNCATED_IMAGES = True

orb = cv2.ORB_create()
bfm = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


@ExceptionWrapper
def compute_image(raw_image: bytes) -> Tuple[Mat, Iterable[Mat], Mat]:
    pil = Image.open(io.BytesIO(raw_image))
    rgb_img = np.array(pil, dtype=np.uint8)
    img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
    image = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    keypoints, descriptor = orb.detectAndCompute(image, None)
    return image, keypoints, descriptor
    

@ExceptionWrapper
def match_images(query_descriptor: Mat, train_descriptor: Mat) -> Iterable[Mat]:
    matches = bfm.match(query_descriptor, train_descriptor)
    matches = sorted(matches, key = lambda x:x.distance)
    best_matches = matches[:MATCH_FILTER]
    return best_matches


@ExceptionWrapper
def estimate_difference(matches: Iterable[Mat],
        query_keypoints: Iterable[Mat], train_keypoints: Iterable[Mat]) -> Tuple[Mat, float, float]:
    
    N = len(matches)
    leftx = np.zeros((N,3))
    rightx = np.zeros(N)
    lefty = np.zeros((N,3))
    righty = np.zeros(N)

    for i, m in enumerate(matches):
        sx, sy = map(int, query_keypoints[m.queryIdx].pt)
        ex, ey = map(int, train_keypoints[m.trainIdx].pt)

        leftx[i] = [sx, sy, 1.]
        rightx[i] = ex
        lefty[i] = [sx, sy, 1.]
        righty[i] = ey
    
    try:
        r1, re1, _, _ = np.linalg.lstsq(leftx, rightx)  # x, residuals, rank, singular
        r2, re2, _, _ = np.linalg.lstsq(lefty, righty)
        
    except np.linalg.LinAlgError:
        logger.info('LinAlgError')
        r1 = np.array([1., 0., 0.])
        r2 = np.array([0., 1., 0.])
        re1 = re2 = [np.Infinity]
    
    return np.array([
        r1,
        r2,
        np.array([0., 0., 1.])
    ]), re1[0], re2[0]
    

@ExceptionWrapper
def decompose_transform(matrix: Mat) -> Tuple[Mat, Mat, Mat]:
    trans = matrix[:,2][:2]
    scale = np.array([
        np.linalg.norm(matrix[:,0][:2]),
        np.linalg.norm(matrix[:,1][:2])
    ])
    rotate = np.stack([
        matrix[:,0] / scale[0],
        matrix[:,1] / scale[1],
        np.array([0., 0., 1.])
    ], axis=0).T
    return trans, scale, rotate