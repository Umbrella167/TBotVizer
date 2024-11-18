import random
import time


from utils.node_utils.BaseFunc import BaseFunc



class RandomInt(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_data = {"res": None}
        self.output_type = {"res": "int"}
        self.running = False
        self.last_time = time.time()
        self.automatic = True

    def calc(self):
        if self.automatic and time.time() - self.last_time > 0.5:
            self.output_data["res"] = random.randint(0, 100)
            self.last_time = time.time()
