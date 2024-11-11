from utils.DataProcessor import TBKData


class Box(object):
    def __init__(self, tbk_data: TBKData):
        self._tbk_data = tbk_data

    def draw(self):
        # 绘制盒子
        raise f"{self.__name__} does not implement draw()"

    def show(self):
        pass

    def update(self):
        # 更新数据
        raise f"{self.__name__} does not implement update()"

    def destroy(self):
        # 销毁盒子
        pass
