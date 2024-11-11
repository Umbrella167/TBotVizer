from typing import List

from config import BaseConfig
from ui.boxes import Box


class UiConfig(BaseConfig):
    def __init__(self, boxes: List[Box]=None):
        # TODO: 长宽应该根据系统长宽设定
        super().__init__()
        self.boxes = boxes
