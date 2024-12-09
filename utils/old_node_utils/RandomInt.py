import random
import time

from config.SystemConfig import run_time
from utils.node_utils.BaseNode import BaseNode


class RandomInt(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_data = {"res": None}
        self.automatic = True

    def calc(self):
        super().calc()
        if self.automatic and (self.parent.now_time - run_time) % 0.5 < 0.01:
            self.output_data["res"] = random.randint(0, 100)
