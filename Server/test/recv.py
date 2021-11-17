import socket
import numpy as np

import io
from PIL import Image, ImageFile
import cv2

from queue import Queue
import threading

import traceback
import os

from calc import estimate_diff2

PORT = 50020
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MATCH_FILTER = 30

def image_reciver(port: int, message_que: Queue, result_que: Queue) -> None:
    def recv_int(sock: socket.socket) -> int:
        data = sock.recv(4)
        return int.from_bytes(data, 'little')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
        serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        serv_sock.bind(('', port))
        serv_sock.listen(1)
        cli_sock, cli_addr = serv_sock.accept()
        print(f'Connect to {cli_addr}')

        try:
            raws = []
            header = b'\xff\xd8\xff'
            while True:
                if not message_que.empty():
                    msg = message_que.get()
                    if msg == 'q':
                        break

                #filesize = recv_int(cli_sock)

                #width = recv_int(cli_sock)
                #height = recv_int(cli_sock)

                raw = cli_sock.recv(1024)
                idx = raw.find(header)
                if idx < 0:
                    raws.append(raw)
                else:
                    raws.append(raw[:idx])
                    full_raw = b''.join(raws)

                    if len(full_raw) > 0:
                        #print(f'Image size : {len(full_raw)}')
                        result_que.put(full_raw)

                    raws.clear()
                    raws.append(raw[idx:])
                
                #raw = cli_sock.recv(filesize)
                #result_que.put(raw)
                
                '''
                pil = Image.open(io.BytesIO(raw))
                rgb_img = np.asarray(pil, dtype='uint8')
                img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

                cv2.imshow('', img)
                '''

        except:
            print(traceback.format_exc())
        finally:
            result_que.put('q')
            cli_sock.close()


def message_reciver(port: int, recv_que: Queue, send_que: Queue):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
        serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        serv_sock.bind(('', port))
        serv_sock.listen(1)
        cli_sock, cli_addr = serv_sock.accept()

        cli_sock.setblocking(False)
        print(f'Connect to {cli_addr}')

        try:
            while True:
                if not send_que.empty():
                    msg = send_que.get()
                    if msg == 'q':
                        break

                try:
                    msg = cli_sock.recv(1024)
                    recv_que.put(msg)
                except BlockingIOError:
                    pass

        except:
            print(traceback.format_exc())
        finally:
            recv_que.put('q')
            cli_sock.close()

if __name__ == '__main__':
    msg_que = Queue()
    img_que = Queue()
    img_thr = threading.Thread(target=image_reciver, args=(PORT, msg_que, img_que,))
    img_thr.start()

    send_que = Queue()
    recv_que = Queue()
    msg_thr = threading.Thread(target=message_reciver, args=(PORT+1, recv_que, send_que,))
    msg_thr.start()

    ImageFile.LOAD_TRUNCATED_IMAGES = True

    def is_filled(l: list) -> bool:
        if not isinstance(l, list):
            return False
        return len(l) > 0

    orb = cv2.ORB_create()
    bfm = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    last_detect = (None, None)
    last_img = None

    save_img = False
    save_img_idx = 0
    os.makedirs(f'{BASE_DIR}/save-img', exist_ok=True)
    while os.path.isfile(f'{BASE_DIR}/save-img/{save_img_idx:05d}.png'):
        save_img_idx += 1

    while (cv2.waitKey(1) & 0xFF) != ord('q'):
        if not recv_que.empty():
            msg = recv_que.get().decode('utf-8')
            if msg == 'save':
                save_img = True
            

        if img_que.empty():
            continue

        try:
            pil = Image.open(io.BytesIO(img_que.get()))
            rgb_img = np.array(pil, dtype=np.uint8)
            img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

            cv2.imshow('org', img)

            kp_qry, des_qry = last_detect
            kp_trn, des_trn = orb.detectAndCompute(img, None)

            if last_detect != None and (not des_qry is None and not des_trn is None):
                matches = bfm.match(des_qry, des_trn)
                matches = sorted(matches, key = lambda x:x.distance)
                best_matches = matches[:MATCH_FILTER]

                match_img = cv2.drawMatches(last_img, kp_qry, img, kp_trn, best_matches, None, flags=2)
                cv2.imshow('cmp', match_img)

                vec_img = img.copy()
                diff_pts = []
                for m in best_matches:
                    sx, sy = map(int, kp_qry[m.queryIdx].pt)
                    ex, ey = map(int, kp_trn[m.trainIdx].pt)
                    vec_img = cv2.arrowedLine(vec_img, (sx, sy), (ex, ey), (255, 0, 0), 1)
                    diff_pts.append((sx, sy, ex, ey))
                cv2.imshow('vec', vec_img)
                estimate_diff2(diff_pts)

                src_pts = np.float32([kp_qry[m.queryIdx].pt for m in best_matches])
                dst_pts = np.float32([kp_trn[m.trainIdx].pt for m in best_matches])
                #tr_mat, mask = cv2.findHomography(src_pts, dst_pts)
                tr_mat, mask = cv2.findHomography(dst_pts, src_pts)     # dst -> src transform
                
                h, w, f = img.shape
                f = 100

                cam_mat = np.array([
                    [f, 0, w/2],
                    [0, f, h/2],
                    [0, 0, 1]
                ])
                n, Rs, Ts, Ns = cv2.decomposeHomographyMat(tr_mat, cam_mat)
                # n == 4: WTF ??

                if not mask is None:
                    mask = mask.ravel().tolist()
                    refine_img = cv2.drawMatches(last_img, kp_qry, img, kp_trn, best_matches, None, matchesMask=mask, flags=2)
                    cv2.imshow('refine', refine_img)

            if save_img:
                last_img = img
                last_detect = (kp_trn, des_trn)
                save_img = False

                cv2.imwrite(f'{BASE_DIR}/save-img/{save_img_idx:05d}.png', img)
                save_img_idx += 1

        except:
            print(traceback.format_exc())
            break
    
    msg_que.put('q')
    send_que.put('q')

    