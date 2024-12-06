import random
import time

from config.SystemConfig import run_time
from utils.new_node_test.BaseNode import BaseNode


class RandomInt(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = {
            "res": {"attribute_type": "OUTPUT", "data_type": "FLOAT", "data": 0},
            "pos": {"attribute_type": None, "data_type": "CONFIG", "data": [0, 0]},
        }
        self.automatic = True

    def calc(self):
        super().calc()
        if self.automatic and (self.parent.now_time - run_time) % 0.5 < 0.01:
            self.data["res"]["data"] = random.randint(0, 100)
