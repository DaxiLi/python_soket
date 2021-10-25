import collections
import json
import time

import Msg


class User:
    userName = None  #
    token = ""
    msgs = None

    TIMEOUT = 2
    lastLogin = 0    # 计时器, 收到心跳包 置 5 每隔 1s -1,为 0 时,广播用户已离线

    def __init__(self, name, token):
        self.userName = name
        self.token = token
        self.lastLogin = time.time()
        self.msgs = collections.deque()

    # 返回是否在线
    # 超时即掉线
    def active(self):
        return (time.time() - self.lastLogin) < self.TIMEOUT

    # 向该用户发送消息
    def addMsg(self, name, msg):
        self.msgs.append(Msg.Msg(user_name=name, text=msg).toDic())

    # 获取该用户的所有消息
    def getMsgs(self):
        msg = []
        for i in range(len(self.msgs)):
            msg.append(self.msgs.popleft())
        return msg

    # 获取该用户的 TOKEN
    def getToken(self):
        return self.token

    # 获取 NAME
    def getName(self):
        return self.userName

    # 刷新 HEART
    def heart(self):
        self.lastLogin = time.time()

    def toString(self):
        return json.dumps({
            'userName': self.userName,
            'token': self.token
        })
