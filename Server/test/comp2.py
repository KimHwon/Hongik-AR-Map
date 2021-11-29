import os, sys

sys.path.insert(1, r'C:\Users\HYOWON\codes\ComputerGraphics\Server')
from ImageProcessing import *

import pickle, copyreg
import time

def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)

improc = ImageProcessor(DATABASE)

cand_zones = list(map(chr, range(97, 105))) # a...h

if __name__ == '__main__':
    
    TESTSET = r'C:\Users\HYOWON\codes\ComputerGraphics\Server\save-img\1'
    for fname in os.listdir(TESTSET):
        filename = os.path.join(TESTSET, fname)
        if not os.path.isfile(filename) or not fname.endswith('png'):  
            continue

        with open(filename, 'rb') as fp:
            raw = bytearray(fp.read())

            img = cv2.imread(filename)
            cv2.imshow('start', img)
            
            vec, info = improc.query_image(raw, 'T')
            print(vec)
        
            if cv2.waitKey() & 0xFF == ord('p'):
                break