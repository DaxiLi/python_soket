import json
import select
import socket
import random

import User


class Serve:
    userList = {}
    serve_fd = None
    bad_request = {'status': -1, 'data': {'msg': 'bad request'}}

    # 构造方法
    def __init__(self, _ip='127.0.0.1', _port=8099):
        self.ip = _ip
        self.port = _port

    # 添加在线用户
    def addUser(self, username, token):
        _user = User.User(username, token)
        self.userList[username] = _user
        self.addMsgs(_msg=username + "上线了", _name="system")

    # 删除在线用户
    def delUser(self, username):
        try:
            del self.userList[username]
        except Exception as ex:
            print("error: " + ex)
        self.addMsgs(_msg=username + "下线了", _name="system")

    # 清理不活跃用户
    def checkOnline(self):
        for key in list(self.userList.keys()):
            if self.userList[key].active() is False:
                self.delUser(key)

    # 只返回 活跃用户，并清理不活跃用户
    def getUsers(self):
        users = []
        for key in list(self.userList.keys()):
            # if self.userList[key].active():
            users.append(key)
            # else:
            #     self.delUser(key)
        return users

    # 验证用户身份
    def authenticate(self, name, token):
        if name not in self.userList:
            return False
        if self.userList[name].getToken() == token:
            return True
        print("error: token error")
        return False

    # 对所有用户发送消息
    def addMsgs(self, _msg, _name):
        for k in self.userList:
            self.userList[k].addMsg(msg=_msg, name=_name)

    # 心跳请求
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
        self.userList[user_name].heart()
        return {
            'status': 0,
            'data': {
                'method': 'heart',
                'msg': 'success'
            }
        }
        return self.bad_request

    # post 请求
    def post(self, data):
        print("info: method post=====================")
        if data is None:
            print("post---- data None")
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
        self.addMsgs(_msg=msg, _name=user_name)
        return {
            'status': 0,
            'data': {
                'method': 'post',
                'msg': 'post success'
            }
        }
        return self.bad_request

    def checkUser(self, name):
        if name == "system":
            return True
        return name in self.userList and self.userList[name].active()

    # 登录请求
    def login(self, data):
        print("info: method login")
        if data is None or data['userName'] is None:
            print("error: data error")
            print(data)
            return self.bad_request
        user_name = data['userName']
        # 该用户已存在 且 活跃
        if self.checkUser(user_name):
            return {
                'status': 1,
                'data': {
                    'msg': 'username has exist'
                }
            }
        else:
            token = user_name + generate_random_str(6)
            self.addUser(username=user_name, token=token)
            return {
                'status': 0,
                'data': {
                    'msg': 'login success',
                    'token': token
                }
            }
        # return self.bad_request

    # get 请求，获取信息
    def get(self, data):
        # print("info: get")
        if data is None:
            return self.bad_request
        try:
            token = data['token']
            _user_name = data['userName']
            msg_type = data['type']
        except IOError as err:
            print(err)
            return self.bad_request
        except Exception as err:
            print(err)
            return self.bad_request
        # 验证身份
        if self.authenticate(name=_user_name, token=token) is False:
            return {
                'status': 1,
                'data': {
                    'method': 'get',
                    'msg': 'not allow'
                }
            }
        # 请求的是 MSG
        if msg_type == 'msg':
            # 检测在线用户
            self.checkOnline()
            # print('info: get msg name:', _user_name)
            msgs_tmp = self.userList[_user_name].getMsgs()
            return {
                'status': 0,
                'data': {
                    'msgs': msgs_tmp
                }
            }
        # 请求用户
        elif msg_type == 'user':
            return {
                'status': 0,
                'data': {
                    'users': self.getUsers()
                }
            }
        else:
            return self.bad_request
        # 测试时返回数据
        return self.bad_request

    # 登出方法，立刻注销登录
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
        self.delUser(user_name)
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
        # 解析请求
        try:
            js_data = json.loads(request)
            method = js_data['method']
            data = js_data['data']
        except Exception as ex:
            print("error: in request!")
            print(ex)
            return json.dumps(self.bad_request)
        # 根据请求方法，调用不同的方法处理，并返回结果
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
        # 一个循环，主要是循环监听请求，当有请求时，保存请求数据，攒够一帧开始处理
        while True:
            # sleep(1)
            readable, writeable, exceptional = select.select(inputs, outputs, inputs)
            # 接受数据
            for r in readable:
                # 新连接
                if r is server:
                    conn, addr = r.accept()
                    print("new request")
                    inputs.append(conn)
                    msg_dic[conn] = b''
                # 新请求
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
                    msg_dic[r] += data
                    outputs.append(r)

            for write_fd in writeable:
                # 发送数据
                quests = msg_dic[write_fd].split(b'\r\n')
                # 0 表明未收到 \r\n ，请求不全，继续等待
                if len(quests) <= 1:
                    outputs.remove(write_fd)
                    continue
                msg_dic[write_fd] = quests[len(quests) - 1]
                del quests[len(quests) - 1]
                # 逐个处理请求
                # 分割请求
                for q in quests:
                    if q == b'':
                        continue
                    else:
                        try:
                            # 开始处理
                            request = self.request(q.decode("utf8")) + '\r\n'
                            write_fd.send(request.encode("utf8"))
                        except Exception as ex:
                            print(str(ex))
                            request = json.dumps(self.bad_request) + '\r\n'
                            write_fd.send(request.encode("utf8"))
                # 处理完毕，将连接移除，避免重复处理
                outputs.remove(write_fd)

            for e in exceptional:
                # 保存出错的队列
                if e in outputs:
                    outputs.remove(e)
                if e in writeable:
                    writeable.remove(e)
                inputs.remove(e)
                del msg_dic[e]


#  生成指定长度的随机字符串
def generate_random_str(randomlength=6):
    random_str = 'T'
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str
