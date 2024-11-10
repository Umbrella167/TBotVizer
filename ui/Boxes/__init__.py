from utils.CallBack import CallBack
from utils.DataProcessor import TBKData
from ui.LayoutManager import LayoutConfig, LayoutManager
from collections import deque


class Box(object):
    def __init__(self, layout_manager: LayoutManager, tbk_data: TBKData):
        self._tbk_data = tbk_data
        self._layout_manager = layout_manager
        self._callback = CallBack(layout_manager)
        # self._theme = theme
        self.maxlen = 5
        self.table_change_list = deque(maxlen=self.maxlen)

    def draw(self):
        # 绘制盒子
        raise f"{self.__name__} does not implement draw()"

    def update(self):
        # 更新数据
        raise f"{self.__name__} does not implement update()"

    def destroy(self):
        # 销毁盒子
        pass
