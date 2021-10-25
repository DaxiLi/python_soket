
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
# 发送 MSG
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


# 发送请求
# 所有的网络请求，必须由此方法发出并返回
def request(msg):
    global send_flag
    global serve_fd
    # 等待锁释放
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


# 连接服务器，并将连接保存 全局变量 serve——fd
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


# 画 main 窗口
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


# 向面板插入一条用户
def insertUser(username):
    global userList
    userList.insert(END, username)


# 向面板插入一条消息
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


# 向右侧用户列表删除一个用户
def delUser(username):
    global userList
    for i in range(0, userList.size()):
        if userList.get(i) == username:
            userList.delete(i)
            return


def userList(main_box):
    user_list = Listbox(main_box, width=14, height=25, bg='yellow', yscrollcommand=True)
    user_list.grid(row=0, column=1, padx=0, pady=0, sticky=S + N)
    user_list.insert("end", user_name)
    user_list.insert("end", "flag")


# 画顶部大框，包括消息展示框体 和 用户列表框体
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


# 点击发送消息
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
    # 向服务器发送请求
    res = request(data)
    # 将消息框清零
    click_clear(box)


# 将消息框清零
def click_clear(box):
    box.delete('1.0', 'end')


# 画底部框体，包括打字区和发送按钮
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


# 获取在线用户列表
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


# 获取本用户的未读消息
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


# 发送心跳包
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


# 发送 MSG
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


# 发送登录请求
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


# 开启多线程循环处理 消息和请求
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

    topBox(winMain)
    bottomBox(winMain)

    req = threading.Thread(target=requestServe)
    req.setDaemon(True)
    req.start()
    winMain.mainloop()


def afterLogin():
    print("after login")
    drawMainBox()


def click_login(entry, serve_addr):
    print("btn login")
    # 一堆校验 输入的用户名和ip地址是否合法
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
    # 登录
    res = login(user_name)
    # 登录成功后 跳转 afterLogin
    if res:
        winLogin.destroy()
        afterLogin()


def draw_login_window():
    print("main windows")
    global winLogin
    winLogin = Tk()
    winLogin.title("login")
    Label(winLogin).grid(column=0, row=0)
    Label(winLogin).grid(column=10, row=8)
    Label(winLogin, text="用户名").grid(column=4, row=1)
    name = StringVar()
    entry = Entry(winLogin, textvariable=name)
    entry.grid(column=5, row=1)
    name.set('aja')
    Label(winLogin, text="服务器地址").grid(column=4, row=0)
    serve_addr = StringVar()
    serve_entry = Entry(winLogin, textvariable=serve_addr)
    serve_addr.set('127.0.0.1:8099')
    serve_entry.grid(column=5, row=0)
    # 添加一个输入框
    Button(winLogin, text="登录", command=lambda: click_login(entry, serve_addr)).grid(column=4, row=3)
    # 添加按钮
    Button(winLogin, text="Quit", command=winLogin.destroy).grid(column=6, row=3)


def main():
    print("start client")
    # 先画出登录窗口
    draw_login_window()
    # 开始登录窗口循环
    # 点击登录以后 跳转到 click_login()
    # 登录成功后 跳转 afterLogin()
    # 画出 main 窗口
    # 开启新线程进行循环监听消息与发送消息
    # 新线程 方法名 是
    winLogin.mainloop()


if __name__ == '__main__':
    # 从这里开始
    main()