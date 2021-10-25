import time


class Msg:
    time = None
    text = None
    user_name = ""

    def __init__(self, user_name, text):
        self.time = time.time()
        self.text = text
        self.user_name = user_name

    def toString(self):
        data = json.dumps({'userName': self.user_name, 'timestmp': self.time, 'text': self.text})
        return data

    def toDic(self):
        return {'userName': self.user_name, 'text': self.text, 'timestmp': self.time}

