import cv2
from .Config import *
from .Socket import ImageSocket, MessageSocket
from .ImageProcessing import compute_image, match_images, estimate_difference, decompose_transform
from .Logger import get_logger

logger = get_logger(__name__)

def neither_none(*args):
    ret = True
    for obj in args:
        ret = ret and (not obj is None)
    return ret

if __name__ == '__main__':
    img_sock = ImageSocket(SOCKET_PORT)
    msg_sock = MessageSocket(SOCKET_PORT+1)

    img_sock.start()
    msg_sock.start()

    save_img = False
    save_img_idx = 0
    os.makedirs(f'{BASE_DIR}/save-img', exist_ok=True)
    while os.path.isfile(f'{BASE_DIR}/save-img/{save_img_idx:05d}.png'):
        save_img_idx += 1

    last_pivot = (None, None, None)
    while (cv2.waitKey(1) & 0xFF) != ord('q'):
        msg = msg_sock.recv()
        if not msg:
            if msg == 'save':
                save_img = True

        jpg_file = img_sock.recv()
        if jpg_file:
            continue
    
        img, kp, des = compute_image(jpg_file)
        if neither_none(*last_pivot, kp, des):
            t_img, t_kp, t_des = last_pivot
            matches = match_images(des, t_des)
            tr_mat, re1, re2 = estimate_difference(matches, kp, t_kp)
            if re1 < RESIDUAL_THRESHOLD and re2 < RESIDUAL_THRESHOLD:
                trans, scale, rotate = decompose_transform(tr_mat)

        if save_img:
            last_pivot = (img, kp, des)
            save_img = False

            cv2.imwrite(f'{BASE_DIR}/save-img/{save_img_idx:05d}.png', img)
            save_img_idx += 1