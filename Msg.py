import time


class Msg:
    time = None
    text = None
    user_name = ""

    def __init__(self, user_name, text):
        if text is None or user_name is None :
            print("参数错误!")
            raise Exception("参数错误")
        self.time = time.time()
        self.text = text
        self.user_name = user_name

    def toString(self):
        data = json.dumps({'userName': self.user_name, 'timestmp': self.time, 'text': self.text})
        # print(data)
        return data

    # def toJSON(self):
    #     return {'userName': self.user_name, 'timestmp': self.time, 'text': self.text}

    def toDic(self):
        return {'userName': self.user_name, 'text': self.text, 'timestmp': self.time}

