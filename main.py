import threading
import time

import User
from Serve import  Serve


def tset_user():
    user = User.User('aja', 'token')
    print(user.toString())
    print(user.getMsgs())
    user.addMsg(name='aja', msg='text')
    user.addMsg(name='aja', msg='text')
    user.addMsg(name='aja', msg='text')
    user.addMsg(name='aja', msg='text')
    print(user.getMsgs())


if __name__ == '__main__':
    print('PyCharm')
    tset_user()

    t1 = time.time()
    print(t1)
    time.sleep(5)
    t2 = time.time()
    print(t2)
    print(t1 - t2)
    print(str(time.time()))
    serve = Serve()
    serve.start()
    # main = threading.Thread(target=serve.start())
    # main.setDaemon(True)
    # main.start()
    while True:
        time.sleep(2)


