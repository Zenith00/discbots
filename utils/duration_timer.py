import datetime
import random
class timer:
    def __init__(self, dur):
        self.time = datetime.datetime.utcnow()
        self.duration = dur

    def set_time(self, duration):
        self.duration = duration
        self.basedur = duration

    def is_next(self):
        current_time = datetime.datetime.utcnow()
        # print("CT: " + str(current_time))
        # print("LT: " + str(current_time))
        timediff = current_time - self.time
        print(timediff.total_seconds())

        if timediff.total_seconds() > self.duration:
            self.time = current_time
            self.duration = random.randint(self.basedur-200, self.basedur+200)
            return True
        else:
            return False