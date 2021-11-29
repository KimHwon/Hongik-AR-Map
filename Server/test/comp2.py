import os, sys

sys.path.insert(1, r'C:\Users\HYOWON\codes\ComputerGraphics\Server')
from ImageProcessing import *

import pickle, copyreg
import time

def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)

improc = ImageProcessor('database.pickle')

cand_zones = list(map(chr, range(97, 105))) # a...h

def test(img):
    kp, des = improc.orb.detectAndCompute(img, None)
    h,w,_ = img.shape

    dist_sum = []
    for z in cand_zones:
        for idx, data in improc.database[z].items():
            if (matches := improc.match_images(des, data['des'])) is None:
                continue
            dsum = sum([m.distance for m in matches])
            dist_sum.append((z, idx, dsum))

    for z, i, dsum in sorted(dist_sum, key=lambda tp : tp[2]):
        match_img = cv2.drawMatches(img, kp, improc.database[z][i]['img'], improc.database[z][i]['kp'], matches, None, flags=2)
        Tr, r1, r2 = improc.estimate_difference(matches, kp, improc.database[z][i]['kp'])
        print((dsum, r1, r2)) # dsum > 700: not sure, r1 or r2 > 200000: not sure
        cv2.imshow('match', match_img)
        if cv2.waitKey() & 0xFF == ord('q'):
            break

if __name__ == '__main__':
    
    TESTSET = r'C:\Users\HYOWON\codes\ComputerGraphics\Server\save-img\1'
    for fname in os.listdir(TESTSET):
        filename = os.path.join(TESTSET, fname)
        if not os.path.isfile(filename) or not fname.endswith('png'):  
            continue
        
        img = cv2.imread(filename)
        cv2.imshow('start', img)
        if cv2.waitKey() & 0xFF == ord('p'):
            break

        #test(img)
        improc.query_image(img)