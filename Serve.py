import json
import queue
import select
import socket
import threading
import random
from time import sleep

import User


class Serve:
    # 在线用户列表 字典 键值是 token , value 是 user class
    # ****** 键名 是用户名 键值 是 socket_fd
    userList = {}
    serve_fd = None
    bad_request = {'status': -1,'data': {'msg': 'bad request'}}
    # sendFlag = {}

    def __init__(self, _ip='127.0.0.1', _port=8099):
        self.ip = _ip
        self.port = _port

    def addUser(self, username, token):
        user = User.User(username)
        # user.socket_fd = fd
        self.userList[token] = user
        self.addMsgs(msg=username + "上线了", name="system")
        # print(self.userList)

    def delUser(self, username):
        try:
            del self.userList[username]
        except Exception as ex:
            print("error: " + ex)
        self.addMsgs(msg=username + "下线了", name="system")

    #  只返回 活跃用户，并清理不活跃用户
    def getUsers(self):
        users = []
        for key in list(self.userList.keys()):
            if self.userList[key].active():
                users.append(self.userList[key].getName())
            else:
                self.delUser(key)
        return users

    def authenticate(self, name, token):
        print("info: authenticate")
        if token not in self.userList:
            print("not user list")
            return False
        # print(self.userList[token].getName())
        # print(name)
        # print(self.userList[token].getName() == name)
        if self.userList[token].getName() == name:
            return True
        print("token error")
        return False

    def addMsgs(self, msg, name):
        for u in self.userList:
            print("u addmsg")
            self.userList[u].addMsg(name=name, msg=msg)

    def heart(self, data):
        print("info: method heart")
        if data is None:
            return self.bad_request
        try:
            token = data['token']
            user_name = data['userName']
        except IOError as err:
            print(err)
            return self.bad_request
        except Exception as err:
            print(err)
            return self.bad_request
        if self.authenticate(name=user_name, token=token) is False:
            return {
                'status': 1,
                'data': {
                    'method': 'heart',
                    'msg': 'not allow'
                }
            }
        self.userList[token].heart()
        return {
            'status': 0,
            'data': {
                'method': 'heart',
                'msg': 'success'
            }
        }
        return self.bad_request

    def post(self, data):
        print("info: method post")
        if data is None:
            return self.bad_request
        try:
            token = data['token']
            user_name = data['userName']
            msg = data['msg']
        except IOError as err:
            print(err)
            return self.bad_request
        except Exception as err:
            print(err)
            return self.bad_request
        if self.authenticate(name=user_name, token=token) is False:
            return {
                'status': 1,
                'data': {
                    'method': 'post',
                    'msg': 'not allow'
                }
            }
        self.addMsgs(msg=msg, name=user_name)
        return {
                'status': 0,
                'data': {
                    'method': 'post',
                    'msg': 'post success'
                }
            }
        return self.bad_request

    def login(self, data):
        print("info: method login")
        if data is None or data['userName'] is None:
            print("error: data error")
            return self.bad_request
        user_name = data['userName']
        # 该用户已存在 且 活跃
        if user_name in self.userList and self.userList[user_name].active():
            return {
                'status': 1,
                'data': {
                    'msg': 'username has exist'
                }
            }
        else:
            token = generate_random_str(12)
            while token in self.userList:
                token = generate_random_str(12)
            # self.userList[token] = User.User(name=user_name)
            self.addUser(username=user_name, token=token)
            print(self.userList)
            return {
                'status': 0,
                'data': {
                    'msg': 'login success',
                    'token': token
                }
            }
        # return self.bad_request

    def get(self, data):
        print("info: get")
        if data is None:
            return self.bad_request
        try:
            token = data['token']
            user_name = data['userName']
            msg_type = data['type']
        except IOError as err:
            print(err)
            return self.bad_request
        except Exception as err:
            print(err)
            return self.bad_request
        if self.authenticate(name=user_name, token=token) is False:
            return {
                'status': 1,
                'data': {
                    'method': 'get',
                    'msg': 'not allow'
                }
            }
        print(msg_type)
        if msg_type == 'msg':
            return {
                'status': 0,
                'data': {
                    'msgs': self.userList[token].getMsgs()
                }
            }
        elif msg_type == 'user':
            return {
                'status': 0,
                'data': {
                    'users': self.getUsers()
                }
            }
        else:
            return self.bad_request
        return self.bad_request

    def logout(self, data):
        print("info: method logout")
        if data is None:
            return self.bad_request
        try:
            token = data['token']
            user_name = data['userName']
        except IOError as err:
            print(err)
            return self.bad_request
        except Exception as err:
            print(err)
            return self.bad_request
        if self.authenticate(name=user_name, token=token) is False:
            return {
                'status': 1,
                'data': {
                    'method': 'logout',
                    'msg': 'not allow'
                }
            }
        # del self.userList[token]
        self.delUser(token)
        return {
            'status': 0,
            'data': {
                'method': 'logout',
                'msg': 'success'
            }
        }
        return self.bad_request

    # 处理请求，接受字符串，返回字符串
    def request(self, request):
        ret_data = {}
        try:
            js_data = json.loads(request)
            method = js_data['method']
            data = js_data['data']
        except Exception as ex:
            print("error: in request!")
            print(ex)
            return json.dumps(self.bad_request)
        if method is None or data is None:
            return json.dumps(self.bad_request)
        elif method == 'heart':
            return json.dumps(self.heart(data))
        elif method == 'post':
            return json.dumps(self.post(data))
        elif method == 'get':
            return json.dumps(self.get(data))
        elif method == 'login':
            return json.dumps(self.login(data))
        elif method == 'logout':
            return json.dumps(self.logout(data))
        else:
            return json.dumps(self.bad_request)

    # 处理发送的数据，构造为完整一帧之后，交由 request 处理
    def processRequests(self, msg):
        requests = msg.split(b'\r\n')
        ret_data = ''
        if len(requests) <= 1:
            return None, requests
        print(requests)
        msg = requests[len(requests) - 1]
        del requests[len(requests) - 1]
        print(requests)
        for q in requests:
            if q == b'':
                continue
            else:
                ret_data += self.request(q.decode("utf8")) + '\r\n'
        return ret_data.encode("utf8")

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # AF_INET
        # ipv4
        server.bind((self.ip, self.port))
        # 绑定要监听的端口
        server.listen(100)
        # 开始监听 表示可以使用五个链接排队
        # 设置非阻塞模式
        server.setblocking(False)

        msg_dic = {}

        inputs = [server, ]

        outputs = []

        while True:
            # sleep(1)
            readable, writeable, exceptional = select.select(inputs, outputs, inputs)
            for r in readable:
                if r is server:
                    conn, addr = r.accept()
                    print("new request")
                    inputs.append(conn)
                    msg_dic[conn] = b''
                else:
                    try:
                        data = r.recv(1024)
                        # 接受 ’‘ ，客户端断开
                        if data == b'':
                            raise Exception("客户端断开")
                    except Exception as ex:
                        print("error: " + str(ex))
                        if r in outputs:
                            outputs.remove(r)
                        if r in writeable:
                            writeable.remove(r)
                        inputs.remove(r)
                        del msg_dic[r]
                        continue
                    print("recv :")
                    print(data)
                    msg_dic[r] += data
                    outputs.append(r)

            for write_fd in writeable:
                quests = msg_dic[write_fd].split(b'\r\n')
                # 0 表明未收到 \r\n ，请求不全，继续等待
                if len(quests) <= 1:
                    outputs.remove(write_fd)
                    continue
                msg_dic[write_fd] = quests[len(quests) - 1]
                del quests[len(quests) - 1]
                # 逐个处理请求
                for q in quests:
                    if q == b'':
                        continue
                    else:
                        try:
                            print(q)
                            request = self.request(q.decode("utf8")) + '\r\n'
                            write_fd.send(request.encode("utf8"))
                        except Exception as ex:
                            print(str(ex))
                            request = json.dumps(self.bad_request) + '\r\n'
                            write_fd.send(request.encode("utf8"))
                outputs.remove(write_fd)

            for e in exceptional:
                if e in outputs:
                    outputs.remove(e)
                if e in writeable:
                    writeable.remove(e)
                inputs.remove(e)
                del msg_dic[e]


def generate_random_str(randomlength=6):
    random_str = 'T'
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str