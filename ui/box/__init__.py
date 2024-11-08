from ui.Components import DiyComponents
from utils.CallBack import CallBack
# from ui.Ui import CallBack
from utils.DataProcessor import UiData, TBKData
from api import TBKApi
from collections import deque


class Box(object):
    def __init__(self, uidata: UiData, tbkdata: TBKData):
        self._uidata = uidata
        self._tbkdata = tbkdata
        self._layout_manager = self._uidata.layout_manager
        self._diycomponents = DiyComponents(self._uidata)
        self._callback = CallBack(self._uidata, self._diycomponents)
        # self._theme = theme
        self.maxlen = 5
        self.table_change_list = deque(maxlen=self.maxlen)

    def draw(self):
        # 绘制盒子
        pass

    def update(self):
        # 更新数据
        pass

    def destroy(self):
        # 销毁盒子
        pass
