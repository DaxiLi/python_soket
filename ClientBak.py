
import base64

import sys
import time
from tkinter import *
import tkinter.messagebox
from time import sleep
import json
import socket
import threading

# 全局变量
SOFTNAME = "HAHAHAH"
send_flag = False
LOCK = threading.Lock()
token = ""
serve_fd = None
winLogin = None
winMain = None
msgList = None
userList = []
serve_ip = "127.0.0.1"
serve_port = 8099
user_name = None
msgBox = None  # 消息框体


# msg 是字典
def sendMsg(conn, msg):
    try:
        data = json.dumps(msg)
        data += '\r\n'
    except IOError as ex:
        print("json dumps error" + ex)
        return
    try:
        conn.send(data.encode("utf8"))
    except:
        print("断开链接")


# 接受一段 以 \r\n 分割的 msg
# return str
# 连接关闭 return -1
# 出错 返回 ""
def recvMsg(conn):
    ret_val = "".encode()
    try:
        while getattr(conn, '_closed') is False:
            msg_char = conn.recv(1)
            if msg_char == b'\r':
                if conn.recv(1) == b'\n':
                    return ret_val.decode("utf8")
                else:
                    ret_val += b'r' + msg_char
            else:
                ret_val += msg_char
    except IOError as err:
        print(err)
        return None
    return None


# 所有的网络请求，必须由此方法发出并返回
def request(msg):
    global send_flag
    global serve_fd
    while send_flag:
        pass
    LOCK.acquire()
    send_flag = True
    if serve_fd is None or getattr(serve_fd, '_closed'):
        try:
            connectServe()
        except Exception as ex:
            print(ex)
            return None
    sendMsg(serve_fd, msg)
    res = recvMsg(serve_fd)
    if res is None:
        return None
    try:
        js_res = json.loads(res)
    except IOError as err:
        print(err)
        return None
    send_flag = False
    LOCK.release()
    return js_res


def connectServe():
    global serve_fd
    try:
        serve_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serve_fd.connect((serve_ip, serve_port))
    except:
        print("建立链接失败")
        # tkinter.messagebox.showerror("错误", '连接到服务器出错!')
        return False
    return True


def draw_window():
    print("draw window")


# 传入 ip 地址
# 合法 return True 否则 False
def checkIP(ip):
    ip_list = ip.split('.')
    if len(ip_list) != 4:
        return False
    for val in ip_list:
        try:
            int(val)
        except:
            return False
    return True


def insertUser(username):
    global userList
    userList.insert(END, username)


def insertMsg(context, user: str, stmp):
    global msgBox
    global user_name
    msgBox.config(state=NORMAL)
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stmp))
    if user == 'system':
        msgBox.insert(END, user + " " + t + "\n", 'redcolor')
        msgBox.insert(END, context + "\n\n", 'redcolor')
        sts = context[-3: -1]
        name = context[0: -3]
        if name == user_name:
            pass
        elif sts == '上线':
            insertUser(name)
        elif sts == '下线':
            delUser(name)
    else:
            msgBox.insert(END, user + " " + t + "\n", 'bluecolor')
            msgBox.insert(END, context + "\n\n")
    msgBox.config(state=DISABLED)
    msgBox.see(END)


def delUser(username):
    global userList
    for i in range(0, userList.size()):
        if userList.get(i) == username:
            userList.delete(i)
            return


def userList(main_box):
    # user_box = Frame(top_box, width=100, height=450, bg='blue')
    user_list = Listbox(main_box, width=14, height=25, bg='yellow', yscrollcommand=True)
    # msg_box.grid(row=0, column=0, padx=0, pady=0)
    # user_box.grid(row=0, column=1, padx=0, pady=0)
    user_list.grid(row=0, column=1, padx=0, pady=0, sticky=S + N)
    user_list.insert("end", user_name)
    user_list.insert("end", "flag")


def msgList(main_box):
    pass


def topBox(main_box):
    # 顶部大框
    global msgBox
    global userList
    top_box = Frame(main_box)
    top_box.pack()

    top_left_box = Frame(top_box)
    top_left_box.grid(column=0, row=0, sticky=N + S + W + E)

    top_right_box = Frame(top_box)
    top_right_box.grid(column=1, row=0, sticky=N + S + W + E)

    msgBox = Text(top_left_box, width=90, height=35)
    msgBox.config(state=DISABLED)
    msgBox.tag_configure('bluecolor', foreground='blue')
    msgBox.tag_configure('redcolor', foreground='red')
    msgBox.pack()

    userList = Listbox(top_right_box, width=14, height=25, bg='yellow', yscrollcommand=True)
    userList.pack()


def click_send(box):
    msg = box.get("1.0", "end")
    print("info: send: " + msg)
    data = {
        'method': 'post',
        'data': {
            'userName': user_name,
            'msg': msg,
            'token': token
        }
    }
    res = request(data)
    click_clear(box)


def click_clear(box):
    box.delete('1.0', 'end')


def bottomBox(main_box):
    text_box = Frame(main_box, width=800, height=100, bg='yellow')
    text_box.pack()

    content_box = Text(text_box, wrap='word', width=100, height=7)
    content_box.grid(row=0, column=0)

    button_box = Frame(text_box, width=100, height=100, bg='black')
    button_box.grid(row=0, column=1)
    # button_box.pack()

    Button(button_box, text="发送", command=lambda: click_send(content_box)).pack()
    Button(button_box, text="清空", command=lambda: click_clear(content_box)).pack()


def getUsers():
    print("get users")
    data = {
        'method': 'get',
        'data': {
            'type': 'user',
            'userName': user_name,
            'token': token
        }
    }
    res = request(data)
    try:
        sts = res['status']
        if sts == 1:
            login(user_name)
        elif sts != 0:
            print("bad request")
            return []
        else:
            data = res['data']['users']
            data.remove(user_name)
    except Exception as ex:
        print(ex)
        return []
    return data


def getMsgs():
    data = {
        'method': 'get',
        'data': {
            'type': 'msg',
            'userName': user_name,
            'token': token
        }
    }
    res = request(data)
    try:
        sts = res['status']
        if sts != 0:
            print("bad request")
            return []
        else:
            data = res['data']['msgs']
    except Exception as ex:
        print(ex)
        return []
    return data


def heart():
    req = {
        'method': 'heart',
        'data': {
            'userName': user_name,
            'token': token
        }
    }
    res = request(req)
    if res['status'] == 0:
        return True
    else:
        return False


def post(_msg):
    print("post msg")
    req = {
        'method': 'post',
        'data': {
            'userName': user_name,
            'token': token,
            'msg': _msg
        }
    }
    print(req)
    res = request(req)
    if res['status'] == 0:
        return True
    else:
        print("error: post", res)
        return False


def login(username):
    req = {
        'method': 'login',
        'data': {
            'userName': username
        }
    }
    res = request(req)
    global token
    global user_name
    user_name = username
    try:
        status = res['status']
        msg = res['data']['msg']
        if status == 0:
            token = res['data']['token']
    except Exception as err:
        msg = "数据错误"
        print("json parse fail!")
        tkinter.messagebox.showerror("错误", str(err))
        return False
    if status != 0:
        tkinter.messagebox.showerror("错误", msg)
        return False
    # tkinter.messagebox.showinfo("成功", "成功")
    return True


def requestServe():
    users = getUsers()
    insertUser(user_name + " - 本机")
    for u in users:
        insertUser(u)
    flag = 0
    while True:
        sleep(0.5)
        flag += 1
        if flag == 2:
            heart()
            flag = 0
        msgs = getMsgs()
        for m in msgs:
            insertMsg(m['text'], m['userName'], m['timestmp'] )


def drawMainBox():
    global winMain
    global SOFTNAME
    global user_name
    winMain = Tk()
    winMain.title(SOFTNAME)
    # winMain.geometry("800x550")

    topBox(winMain)
    bottomBox(winMain)

    req = threading.Thread(target=requestServe)
    req.setDaemon(True)
    req.start()
    # req.
    winMain.mainloop()


def afterLogin():
    print("after login")
    drawMainBox()


def click_login(entry, serve_addr):
    print("btn login")
    global user_name
    user_name = entry.get()
    print("username: " + user_name)
    print("serve addr : " + serve_addr.get())
    tmp = serve_addr.get().split(':')
    if checkIP(tmp[0]) is False:
        tkinter.messagebox.showerror("错误", '请输入正确的ip')
        return
    # 检查 端口号 和服务器地址
    global serve_ip
    serve_ip = tmp[0]
    try:
        global serve_port
        serve_port = int(tmp[1])
        if serve_port < 1 or serve_port > 65534:
            raise Exception
    except:
        tkinter.messagebox.showerror("错误", '请输入正确的端口号')
        return
    # 建立链接
    if connectServe() is False:
        tkinter.messagebox.showerror("错误", "连接到主机失败!")
        return
    # 检查 用户名
    if len(user_name) == 0:
        tkinter.messagebox.showerror("错误", "请输入用户名")
        return
    res = login(user_name)
    if res:
        winLogin.destroy()
        afterLogin()


def draw_login_window():
    print("main windows")
    global winLogin
    winLogin = Tk()
    winLogin.title("login")
    # 新建窗口
    # winLogin.grid_con
    # winLogin.geometry("400x150")
    # 调整大小
    Label(winLogin).grid(column=0, row=0)
    Label(winLogin).grid(column=10, row=8)
    Label(winLogin, text="用户名").grid(column=4, row=1)
    name = StringVar()
    entry = Entry(winLogin, textvariable=name)
    entry.grid(column=5, row=1)
    # ######################### TEST
    name.set('aja')
    # ######################### TEST End
    Label(winLogin, text="服务器地址").grid(column=4, row=0)
    serve_addr = StringVar()
    serve_entry = Entry(winLogin, textvariable=serve_addr)
    serve_addr.set('127.0.0.1:8099')
    serve_entry.grid(column=5, row=0)
    # 添加一个输入框
    Button(winLogin, text="登录", command=lambda: click_login(entry, serve_addr)).grid(column=4, row=3)
    # 添加按钮
    Button(winLogin, text="Quit", command=winLogin.destroy).grid(column=6, row=3)

    # ###### TEST
    winLogin.mainloop()



def main():
    print("start client")
    draw_login_window()
    # sleep(5000)



def test():
    client = socket.socket()
    client.connect(('127.0.0.1', 8099))
    data = {
        'method': 'login',
        'data': {
            'userName': 'aja'
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    # sendMsg(client, data)
    back_message = recvMsg(client)
    print(back_message)
    js_data = json.loads(back_message)
    res = js_data['status']
    token = "TEQC25CdfbG0m"
    if res == 0:
        token = js_data['data']['token']
    print(token)

    data = {
        'method': 'get',
        'data': {
            'type': 'msg',
            'userName': 'aja',
            'token': token
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    data = {
        'method': 'post',
        'data': {
            'type': 'msg',
            'userName': 'aja',
            'token': token,
            'msg': 'test msg'
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    data = {
        'method': 'get',
        'data': {
            'type': 'msg',
            'userName': 'aja',
            'token': token
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    data = {
        'method': 'heart',
        'data': {
            'type': 'msg',
            'userName': 'aja',
            'token': token
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    data = {
        'method': 'get',
        'data': {
            'type': 'user',
            'userName': 'aja',
            'token': token
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    # BAD REQUEST TEST ++++++++++++++++++++++++++++
    data = {
        'method': 'gethhh',
        'data': {
            'type': 'user',
            'userName': 'aja',
            'token': token
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    data = {
        'method': 'get',
        'data': {
            'type': 'usker',
            'userName': 'aja',
            'token': token
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    data = {
        'method': 'post',
        'data': {
            'type': 'user'
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    data = {
        'method': 'get',
        'data': {
            'type': 'user',
        }
    }
    client.send((json.dumps(data) + '\r\n').encode("utf8"))
    print((json.dumps(data) + '\r\n'))
    back_message = recvMsg(client)
    print(back_message)

    sleep(4)
    # exit()




if __name__ == '__main__':
    # res = login('aja')
    # print("login =================== aja")
    # res = getUsers()
    # print(res)
    # res = post('text111')
    # print(res)
    # res = post('text222')
    # print(res)
    # res = post('text333')
    # print(res)
    # res = getMsgs()
    # print(res)
    #
    # res = post('text444')
    # print(res)
    # res = post('text555')
    # print(res)
    #
    # login('buuu')
    # print("login =================== buuuu")
    # res = getUsers()
    # print(res)
    # res = post('text111')
    # print(res)
    # res = post('text222')
    # print(res)
    # res = post('text333')
    # print(res)
    # res = getMsgs()
    # print(res)

    # res = login('su')
    # res = getUsers()
    # print(res)
    # res = post('text su')
    # print(res)
    # res = getMsgs()
    # print(res)

    s = "aja下线了"
    s1 = "aja上线了"

    # print(s[-3: -1])

    main()
    # test()
    sleep(3)


#
# from tkinter import *
# import json
# import socket
# import threading
#
#
# class WinLogin:
#     main = None
#     Master = None
#
#     def __init__(self, master):
#         self.Master = master
#         self.draw()
#         self.main.mainloop()
#
#     def draw(self):
#         print("main windows")
#         self.main = Tk()
#         self.main.title("login")
#         # 新建窗口
#         # self.main.grid_con
#         # self.main.geometry("400x150")
#         # 调整大小
#         Label(self.main).grid(column=0, row=0)
#         Label(self.main).grid(column=10, row=8)
#         Label(self.main, text="用户名").grid(column=4, row=1)
#         name = StringVar()
#         entry = Entry(self.main, textvariable=name)
#         entry.grid(column=5, row=1)
#         # ######################### TEST
#         name.set('aja')
#         # ######################### TEST End
#         Label(self.main, text="服务器地址").grid(column=4, row=0)
#         serve_addr = StringVar()
#         serve_entry = Entry(self.main, textvariable=serve_addr)
#         serve_addr.set('127.0.0.1:8099')
#         serve_entry.grid(column=5, row=0)
#         # 添加一个输入框
#         Button(self.main, text="登录", command=lambda: click_login(self, entry, serve_addr)).grid(column=4, row=3)
#         # 添加按钮
#         Button(self.main, text="Quit", command=lambda: click_quit(self)).grid(column=6, row=3)
#
#         def click_login(self, _entry, _serve_addr):
#             self.Master.click_login(_entry, _serve_addr)
#
#         def click_quit(self):
#             self.Master.click_quit()
#
#         def destroy(self):
#             self.main.destroy()
#
#
# class WinMain:
#     main = None
#
#     def __init__(self):
#         self.draw()
#
#     def draw(self):
#         pass
#
#
# class Client:
#     SOFTNAME = "HAHAHAH"
#     winLogin = None
#     winMain = None
#     msgList = None
#     userList = []
#     serve_ip = "127.0.0.1"
#     serve_port = 8099
#     user_name = None
#     client_fd = -1
#     msgBox = None  # 消息框体
#
#     def __init__(self):
#         self.winLogin = WinLogin(self)
#         pass
#
#     def login(self):
#         self.winLogin.mainloop()
#
#     def click_login(self, _entry, _serve_addr):
#         print("click login")
#
#     def click_quit(self):
#         print("click quit")
#         self.winLogin.destroy()
#
#     #
#     # # 传入 ip 地址
#     # # 合法 return True 否则 False
#     # def checkIP(self, ip):
#     #     ip_list = ip.split('.')
#     #     if len(ip_list) != 4:
#     #         return False
#     #     for val in ip_list:
#     #         try:
#     #             int(val)
#     #         except:
#     #             return False
#     #     return True
#     #
#     # def connectServe(self):
#     #     global client_fd
#     #     try:
#     #         client_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     #         client_fd.connect((serve_ip, serve_port))
#     #     except:
#     #         print("建立链接失败")
#     #         # tkinter.messagebox.showerror("错误", '连接到服务器出错!')
#     #         return False
#     #     return True
#     #
#     # def draw_login_window(self):
#     #     pass
#     #
#     # def login(self):
#     #     print("login")
#     #     self.winMain = WinMain()
#     #
#     # def main(self):
#     #     print("start client")
#     #     login()
#
#
# def main():
#     # TEST
#     log = Client()
#     log.login()
#
#
#
# if __name__ == '__main__':
#     pass
