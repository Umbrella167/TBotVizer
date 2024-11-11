from typing import List

from config import BaseConfig
from config.SystemConfig import config
from ui.LayoutManager import LayoutManager
from ui.boxes import Box


class UiConfig(BaseConfig):
    def __init__(self, title="TBK-ParamManager", boxes: List[Box]=None):
        # TODO: 长宽应该根据系统长宽设定
        super().__init__()
        self.boxes = boxes
        self.layout = LayoutManager()
        self.title = title


