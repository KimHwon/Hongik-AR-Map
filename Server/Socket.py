import socket
from threading import Thread
from queue import Queue
import struct
import traceback
from typing import *

from Config import *
from Logger import get_logger

logger = get_logger(__name__)

class CloseSocket(Exception):
    pass

class AsyncSocket(Thread):
    def __init__(self, port: int, nonblock: bool = False):
        Thread.__init__(self, daemon=True)

        self.send_que = Queue()
        self.recv_que = Queue()

        self.port = port
        self.nonblock = nonblock

    def close(self):
        if self.cli_sock:
            self.cli_sock.close()
        if self.serv_sock:
            self.serv_sock.close()

    def callback(self):
        raise NotImplementedError(self.__class__)

    def run(self):
        self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.serv_sock.bind(('', self.port))
        self.serv_sock.listen(1)

        while True:     # keep try re-connect
            self.cli_sock, cli_addr = self.serv_sock.accept()
            logger.info(f'Connect to {cli_addr}')

            self.cli_sock.setblocking(not self.nonblock)

            while True:
                try:
                    self.callback()
                except BlockingIOError:
                    pass
                except (CloseSocket, ConnectionAbortedError) as err:
                    logger.info(f'Close to {cli_addr}: {err}')
                    self.cli_sock.close()
                    self.cli_sock = None
                    break
                except:
                    logger.error(traceback.format_exc())
                    self.close()
                    return
        
    
    def recv(self) -> Any:
        if not self.recv_que.empty():
            return self.recv_que.get()
        return None
    
    def send(self, data: Any):
        self.send_que.put(data)


class ImageSocket(AsyncSocket):
    JPG_MAGIC  = b'\xff\xd8\xff'

    def __init__(self, port: int):
        AsyncSocket.__init__(self, port, False)
        self.raws = []

    def callback(self):
        if not self.send_que.empty():
            if (msg := self.send_que.get()) == 'q':
                raise CloseSocket()
        
        raw = self.cli_sock.recv(SOCKET_BUFFER)
        if (idx := raw.find(ImageSocket.JPG_MAGIC)) < 0:
            self.raws.append(raw)
        else:
            self.raws.append(raw[:idx])
            full_raw = b''.join(self.raws)

            if len(full_raw) > 0:
                self.recv_que.put(full_raw)

            self.raws.clear()
            self.raws.append(raw[idx:])


class DataSocket(AsyncSocket):
    TEXT    = b'\x01'
    SENSOR  = b'\x02'
    DEST    = b'\x03'
    ETX     = b'\x03'

    def __init__(self, port: int):
        AsyncSocket.__init__(self, port, True)

    def wrap_message(self, msg: str) -> bytes:
        raw = bytearray(SOCKET_BUFFER)
        raw[0] = DataSocket.TEXT
        i = 1
        for b in msg.encode('utf-8'):
            if i >= SOCKET_BUFFER-1:
                break
            raw[i] = b
            i += 1
        raw[i] = DataSocket.ETX
        return bytes(raw)
    
    def wrap_vector(self, vec: list) -> bytes:
        raw = bytearray(SOCKET_BUFFER)
        if len(vec) != 3:
            return bytes(raw)

        raw[0] = DataSocket.SENSOR
        i = 1
        for b in struct.pack('<fff', *vec):
            if i >= SOCKET_BUFFER-1:
                break
            raw[i] = b
            i += 1
        return bytes(raw)
        
    def callback(self):
        raw = self.cli_sock.recv(SOCKET_BUFFER)
        if raw:
            head = raw[0].to_bytes(1, 'little')
        else:
            head = b'\x00'  # lost connection
        
        if head == DataSocket.TEXT:
            idx = raw.find(DataSocket.ETX)
            msg = raw[1:idx].decode('utf-8')
            self.recv_que.put((DataSocket.TEXT, msg))
                
        elif head == DataSocket.SENSOR:
            datas = []
            for i in range(11):
                s, e = i*4+1, i*4+5
                datas.append(struct.unpack('<f', raw[s:e])[0])
            la,lo,al, qw,qx,qy,qz, vx,vy,vz, ry = datas
            self.recv_que.put((DataSocket.SENSOR,
                la,lo,al,       # location
                qw,qx,qy,qz,    # attitude
                vx,vy,vz,       # acceleration
                ry              # compass
            ))

        elif head == DataSocket.DEST:
            conv = {
                b'T': 'T',  # T
                b'S': 'S',  # S
                b'1': '1',  # Z1
                b'2': '2',  # Z2
                b'D': 'D'   # Dorm
            }
            self.recv_que.put((DataSocket.DEST, conv[raw[1]]))

        if not self.send_que.empty():
            msg = self.send_que.get()
            if isinstance(msg, str):
                if msg == 'q':
                    raise CloseSocket()
                else:
                    self.cli_sock.send(self.wrap_message(msg))
            elif isinstance(msg, list):
                self.cli_sock.send(self.wrap_vector(msg))
            else:
                self.cli_sock.send(bytes(SOCKET_BUFFER))
        else:   # if nothing to say, send zero-filled buffer
            self.cli_sock.send(bytes(SOCKET_BUFFER))
        
        