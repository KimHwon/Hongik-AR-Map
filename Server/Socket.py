import socket
from threading import Thread
from queue import Queue
import traceback
from typing import *

from .Config import *
from .Logger import get_logger

logger = get_logger(__name__)

class CloseSocket(Exception):
    pass

class AsyncSocket(Thread):
    def __init__(self, port: int, nonblock: bool = False):
        Thread.__init__(self)

        self.send_que = Queue()
        self.recv_que = Queue()

        self.port = port
        self.nonblock = nonblock

    def callback(self):
        raise NotImplementedError(self.__class__)

    def run(self):
        self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.serv_sock.bind(('', self.port))
        self.serv_sock.listen(1)
        self.cli_sock, cli_addr = self.serv_sock.accept()

        self.cli_sock.setblocking(not self.nonblock)

        while True:
            try:
                self.callback()
            except BlockingIOError:
                pass
            except CloseSocket:
                break
            except:
                logger.error(traceback.format_exc())
                break

        self.cli_sock.close()
        self.serv_sock.close()
    
    def recv(self) -> Any:
        if self.recv_que.not_empty():
            return self.recv_que.get()
        return None
    
    def send(self, data: Any):
        self.send_que.put(data)


class ImageSocket(AsyncSocket):
    def __init__(self, port: int):
        AsyncSocket.__init__(port, False)
        self.raws = []

    def callback(self):
        if self.send_que.not_empty():
            msg = self.send_que.get()
            if msg == 'q':
                raise CloseSocket()
        
        raw = self.cli_sock.recv(SOCKET_BUFFER)
        idx = raw.find(b'\xff\xd8\xff')     # JPG magic bits
        if idx < 0:
            self.raws.append(raw)
        else:
            self.raws.append(raw[:idx])
            full_raw = b''.join(self.raws)

            if len(full_raw) > 0:
                self.recv_que.put(full_raw)

            self.raws.clear()
            self.raws.append(raw[idx:])


class MessageSocket(AsyncSocket):
    def __init__(self, port: int):
        AsyncSocket.__init__(port, True)
        self.raws = []

    def callback(self):
        if self.send_que.not_empty():
            msg = self.send_que.get()
            if msg == 'q':
                raise CloseSocket()
            else:
                self.cli_sock.send(msg.encode('utf-8'))
        
        raw = self.cli_sock.recv(SOCKET_BUFFER)
        idx = raw.find(b'\x03')     # ETX bit
        if idx < 0:
            self.raws.append(raw)
        else:
            self.raws.append(raw[:idx])
            full_raw = b''.join(self.raws)

            if len(full_raw) > 0:
                self.recv_que.put(full_raw.decode('utf-8'))

            self.raws.clear()
            self.raws.append(raw[idx:])