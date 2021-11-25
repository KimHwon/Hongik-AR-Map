import traceback
import numpy as np
from scipy import spatial
import io
from PIL import Image, ImageFile
import cv2

import traceback
from typing import *

from Config import *
from Logger import get_logger

logger = get_logger(__name__)


Mat = np.ndarray
def ExceptionWrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logger.error(traceback.format_exc())
        return None
    return wrapper


orb = cv2.ORB_create(scaleFactor=1.1)
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
        r1, re1, _, _ = np.linalg.lstsq(leftx, rightx, rcond=None)  # x, residuals, rank, singular
        r2, re2, _, _ = np.linalg.lstsq(lefty, righty, rcond=None)
        
    except np.linalg.LinAlgError:
        logger.info('LinAlgError')
        r1 = np.array([1., 0., 0.])
        r2 = np.array([0., 1., 0.])
        re1 = re2 = [np.Infinity]
    
    return np.stack([
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

@ExceptionWrapper
@ExceptionWrapper
def estimate_perspective(matches: Iterable[Mat], query_keypoints: Iterable[Mat], train_keypoints: Iterable[Mat],
    image_shape: Tuple[float, float], normal: Mat) -> Tuple[Mat, Mat, Mat]:

    src_pts = np.array([query_keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2).astype(np.float32)
    dst_pts = np.array([train_keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2).astype(np.float32)

    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC)

    w, h = image_shape
    f = FOCUS_LENGTH
    K = np.array([      # camera intrinsic parameters
        [f, 0, w/2],
        [0, f, h/2],
        [0, 0, 1]
    ])
    n, Rs, Ts, Ns = cv2.decomposeHomographyMat(H, K)
    mxv, mxi = np.Inf, 0
    for i in range(n):
        dist = spatial.distance.cosine(Ns[i], normal)
        if mxv < dist:
            mxv, mxi = dist, i
    
    Tx,Ty,Tz = Ts[mxi]
    T = np.concatenate((Tx,Ty,Tz))
    return H, Rs[mxi], T