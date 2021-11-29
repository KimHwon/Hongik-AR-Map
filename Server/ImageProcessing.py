import numpy as np
from scipy import spatial
import io
from PIL import Image, ImageFile
import cv2
import validators, requests
import pickle, copyreg

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

class ImageProcessor:
    def __init__(self, DB_path: str):
        self.orb = cv2.ORB_create(scaleFactor=1.1)
        self.bfm = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        self.database = self.load_database(DB_path)
    
    def query_image(self, raw_image: bytes, destination: str, zone: str = None) -> Tuple[Mat, Dict]:
        if not destination in ['T', 'S', '1', '2']:
            return np.array([0, 0, 0]), None
        if (res := self.compute_image(raw_image)) is None:
            return np.array([0, 0, 0]), None
        img, kp, des = res
        h,w,_ = img.shape

        if zone is None:
            cand_zones = list(map(chr, range(97, 105))) # a...h
        elif len(zone) == 1:
            cand_zones = [
                zone,
                chr((ord(zone) - 97-1 + 8) % 8 + 97),
                chr((ord(zone) - 97+1 + 8) % 8 + 97)
            ]
        else:
            return np.array([0, 0, 0]), None
        
        dist_sum = []
        for z in cand_zones:
            for idx, data in self.database[z].items():
                if (matches := self.match_images(des, data['des'])) is None:
                    continue
                dsum = sum([m.distance for m in matches])
                dist_sum.append((z, idx, dsum))
        
        for z, i, dsum in sorted(dist_sum, key=lambda tp : tp[2]):
            if dsum < DISTANCE_THRESHOLD:
                Tr, r1, r2 = self.estimate_difference(matches, kp, self.database[z][i]['kp'])
                if r1 < RESIDUAL_THRESHOLD and r2 < RESIDUAL_THRESHOLD:
                    head_vec = self.database[z][i]['dir'][destination]
                    H, R, T = self.estimate_perspective(matches, kp, self.database[z][i]['kp'], (w,h), np.array([0, 0, 1]))
                    return np.dot(R, head_vec) + T, self.database[z][i]
                    
        return np.array([0, 0, 0]), None


    @ExceptionWrapper
    def load_database(self, path: str) -> Dict:
        # Define serializer.
        copyreg.pickle(cv2.KeyPoint().__class__, lambda p: (cv2.KeyPoint, (*p.pt, p.size, p.angle, p.response, p.octave, p.class_id)))

        database = {}
        if validators.url(path):
            res = requests.get(path)
            res.raise_for_status()
            database = pickle.loads(res.content)
        else:
            with open(path, 'rb') as fp:
                database = pickle.load(fp)
        return database

    @ExceptionWrapper
    def compute_image(self, raw_image: bytes) -> Tuple[Mat, Iterable[Mat], Mat]:
        pil = Image.open(io.BytesIO(raw_image))
        rgb_img = np.array(pil, dtype=np.uint8)
        img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
        image = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

        keypoints, descriptor = self.orb.detectAndCompute(image, None)
        return image, keypoints, descriptor
        
    @ExceptionWrapper
    def match_images(self, query_descriptor: Mat, train_descriptor: Mat) -> Iterable[Mat]:
        matches = self.bfm.match(query_descriptor, train_descriptor)
        matches = sorted(matches, key = lambda x:x.distance)
        best_matches = matches[:MATCH_FILTER]
        return best_matches

    @ExceptionWrapper
    def estimate_difference(self, matches: Iterable[Mat],
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
    def decompose_transform(self, matrix: Mat) -> Tuple[Mat, Mat, Mat]:
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
    def estimate_perspective(self, matches: Iterable[Mat], query_keypoints: Iterable[Mat], train_keypoints: Iterable[Mat],
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

