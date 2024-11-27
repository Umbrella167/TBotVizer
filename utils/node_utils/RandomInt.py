import random
import time

from config.SystemConfig import run_time
from utils.node_utils.BaseFunc import BaseFunc


class RandomInt(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_data = {"res": None}
        self.automatic = True

    def calc(self):
        super().calc()
        if self.automatic and (time.time() - run_time) % 0.5 < 0.01:
            self.output_data["res"] = random.randint(0, 100)
