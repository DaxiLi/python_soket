import json
import queue
import threading
import time

import Msg


class User:
    userName = None  #
    socket_fd = None  # 该用户 链接
    callback_fd = None  # 回调 socket
    token = ""
    msgs = queue.Queue()

    _send_flag = False
    _lock = threading.Lock()

    TIMEOUT = 10
    lastLogin = 0
    count = 5           # 计时器, 收到心跳包 置 5 每隔 1s -1,为 0 时,广播用户已离线
    # msg = Queue(maxsize=15)

    def __init__(self, name, token=''):
        self.userName = name
        self.lastLogin = time.time()
        # self.token = token

    def active(self):
        return self.lastLogin - time.time() < self.TIMEOUT

    def addMsg(self, name, msg):
        if self.msgs.full():
            self.msgs.get()
        self.msgs.put(Msg.Msg(user_name=name, text=msg))

    def getMsgs(self):
        msgs = []
        while self.msgs.empty() is False:
            msgs.append(self.msgs.get().toDic())
        return msgs

    def getName(self):
        return self.userName

    def heart(self):
        self.lastLogin = time.time()

    def sendMsg(self, msg):
        if getattr(self.socket_fd, '_closed'):
            print("error: 连接关闭")
            return
        while self._send_flag:
            pass
        self._lock.acquire()
        self._send_flag = True
        try:
            data = json.dumps(msg)
            print("send msg")
            data += '\r\n'
            print(data)
        except:
            print("json dumps error")
            return
        try:
            self.socket_fd.send(data.encode("utf8"))
        except:
            print("断开链接")
        finally:
            self._send_flag = False
            self._lock.release()

    def toString(self):
        return json.dumps({
            'userName': self.userName,
            'token': self.token
        })
