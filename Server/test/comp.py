import os, sys

sys.path.insert(1, r'C:\Users\HYOWON\codes\ComputerGraphics\Server')
from ImageProcessing import *

import pickle, copyreg
import time

def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)

DATABASE = r'C:\Users\HYOWON\codes\ComputerGraphics\Server\save-img\filtered'

database = {}
copyreg.pickle(cv2.KeyPoint().__class__, lambda p: (cv2.KeyPoint, (*p.pt, p.size, p.angle, p.response, p.octave, p.class_id)))

if os.path.isfile('database.pickle'):
    with open('database.pickle', 'rb') as fp:
        database = pickle.load(fp)
else:
    idx = 0
    dir_vec_list = {}
    if os.path.isfile('dir.vec'):
        with open('dir.vec', 'rb') as fp:
            dir_vec_list = pickle.load(fp)
    conv = {
        '2': np.array([0, 0, -1]),
        '4': np.array([1, 0, 0]),
        '6': np.array([-1, 0, 0]),
        '8': np.array([0, 0, 1]),
    }
    conv['1'] = normalize(conv['2'] + conv['4'])
    conv['3'] = normalize(conv['2'] + conv['6'])
    conv['7'] = normalize(conv['4'] + conv['8'])
    conv['9'] = normalize(conv['6'] + conv['8'])

    for zonedir in os.listdir(DATABASE):
        zonename = os.path.join(DATABASE, zonedir)
        if os.path.isdir(zonename):
            for fname in os.listdir(zonename):
                filename = os.path.join(zonename, fname)
                if not os.path.isfile(filename) or not fname.endswith('png'):  
                    continue

                img = cv2.imread(filename)
                kp, des = orb.detectAndCompute(img, None)

                dir_vec = {}
                if idx in dir_vec_list:
                    dir_vec = dir_vec_list[idx]
                else:
                    for dtext in ['T', 'S', '1', '2']:
                        t_img = img.copy()
                        cv2.putText(t_img, dtext, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2)
                        cv2.imshow('dir', t_img)
                        char = chr(cv2.waitKey() & 0xFF)

                        if char == 'q':
                            cv2.destroyAllWindows()
                            exit(0)

                        dir_vec[dtext] = conv[char]
                        dir_vec_list[idx] = dir_vec

                    with open('dir.vec', 'wb') as fp:
                        pickle.dump(dir_vec_list, fp)
                

                database[idx] = {
                    'idx': idx,
                    'path': filename,
                    'zone': zonedir,
                    'dir': dir_vec,
                    'img': img,
                    'kp': kp,
                    'des': des
                }
                print(idx, end='\r')
                idx += 1

    cv2.destroyAllWindows()
    with open('database.pickle', 'wb') as fp:
        pickle.dump(database, fp)

print('Database loaded.')

def test(img):
    kp, des = orb.detectAndCompute(img, None)
    h,w,_ = img.shape

    dist_sum = []
    for idx, data in database.items():
        matches = bfm.match(des, data['des'])
        matches = sorted(matches, key = lambda x:x.distance)
        matches = matches[:MATCH_FILTER]

        dsum = sum([m.distance for m in matches])
        dist_sum.append((idx, dsum))

    srt = sorted(dist_sum, key=lambda tp : tp[1])
    for i, dsum in srt:
        match_img = cv2.drawMatches(img, kp, database[i]['img'], database[i]['kp'], matches, None, flags=2)
        Tr, r1, r2 = estimate_difference(matches, kp, database[i]['kp'])
        print((dsum, r1, r2)) # dsum > 700: not sure, r1 or r2 > 200000: not sure
        cv2.imshow('match', match_img)
        if cv2.waitKey() & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


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

        test(img)
