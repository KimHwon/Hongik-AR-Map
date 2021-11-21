import socket
from threading import Thread
from queue import Queue
import traceback

from .Config import *
from .Logger import GetLogger

logger = GetLogger(__name__)

class AsyncSocket(Thread):
    def __init__(self, port: int, nonblock: bool = False):
        self.send_que = Queue()
        self.recv_que = Queue()

        self.port = port
        self.nonblock = nonblock

        Thread.__init__(self)
    
    def callback(self):
        raise NotImplementedError(self.__class__)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
            serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            serv_sock.bind(('', self.port))
            serv_sock.listen(1)
            cli_sock, cli_addr = serv_sock.accept()

            cli_sock.setblocking(not self.nonblock)

            while True:
                try:
                    self.callback()
                except BlockingIOError:
                    pass
                except:
                    logger.error(traceback.format_exc())
                    break

            cli_sock.close()


class ImageSocket(AsyncSocket):
    def callback(self):
        pass


class MessageSocket(AsyncSocket):
    def callback(self):
        pass