from utils.DataProcessor import TBKData
import dearpygui.dearpygui as dpg


class Box(object):
    def __init__(self, tbk_data: TBKData=None, tag=None, sons=None, data=None, parent=None):
        if data is None:
            data = []
        if sons is None:
            sons = []
        self.tag = tag
        self.parent = parent
        self.sons = sons
        self.tbk_data = tbk_data
        self._data = data

    def show(self):
        # 显示
        # raise f"{self.__name__} does not implement draw()"
        pass

    def create(self):
        # 创建
        pass

    def draw(self):
        # 创建并显示
        # self.create()
        # self.show()
        pass

    def update(self):
        # 更新数据
        raise f"{self.__name__} does not implement update()"

    def destroy(self):
        # 销毁盒子
        pass

    @property
    def x(self):
        return dpg.get_item_pos(self.tag)[0]

    @property
    def y(self):
        return dpg.get_item_pos(self.tag)[1]

    @property
    def data(self):
        return self._data
