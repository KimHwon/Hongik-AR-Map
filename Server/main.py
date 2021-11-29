import cv2
from PIL import ImageFile

from Config import *
from Socket import ImageSocket, DataSocket
from ImageProcessing import ImageProcessor
from Logger import get_logger


logger = get_logger(__name__)

def neither_none(*args):
    ret = True
    for obj in args:
        ret = ret and (not obj is None)
    return ret

if __name__ == '__main__':
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    img_proc = ImageProcessor(DATABASE)

    img_sock = ImageSocket(SOCKET_PORT)
    data_sock = DataSocket(SOCKET_PORT+1)

    img_sock.start()
    data_sock.start()

    last_zone = None
    destination = '*'
    while (cv2.waitKey(1) & 0xFF) != ord('q'):
        if (zipped := data_sock.recv()):
            if zipped[0] == DataSocket.TEXT:
                logger.info(('TEXT', zipped))
                if zipped[1] == 'save':
                    pass
                elif zipped[1] == 'exit':
                    img_sock.send('q')
                    data_sock.send('q')
            elif zipped[0] == DataSocket.SENSOR:
                _, la,lo,al, qw,qx,qy,qz, vx,vy,vz, ry = zipped
                logger.info(('SENSOR', la,lo,al, qw,qx,qy,qz, vx,vy,vz, ry))
            elif zipped[0] == DataSocket.DEST:
                destination = zipped[1]
                logger.info(('DEST', destination))

        jpg_file = img_sock.recv()
        if not jpg_file:
            continue
        
        if destination != '*':
            dir_vec, info = img_proc.query_image(jpg_file, destination, last_zone)
            if not info is None:
                last_zone = info['zone']
                logger.info(last_zone)
            else:
                last_zone = None
                logger.info('Failed to recognize.')
            data_sock.send(dir_vec.tolist())

    
    img_sock.send('q')
    data_sock.send('q')
    