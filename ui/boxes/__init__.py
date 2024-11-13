import dearpygui.dearpygui as dpg


class Box(object):
    def __init__(self, tag=None, parent=None, label=None, callback=None):
        self.tag = tag
        self.parent = parent
        self.label = label
        self.callback = callback
        self.is_created = False
        

    def create(self):
        # 创建
        raise f"{self.__name__} does not implement create()"

    def show(self):
        if not self.is_created:
            self.create()
        # raise f"{self.__name__} does not implement draw()"

    def draw(self):
        # # 创建并显示
        # self.create()
        # self.show()
        pass

    def update(self):
        # 更新数据
        # raise f"{self.__name__} does not implement update()"
        pass

    def destroy(self):
        # 销毁盒子
        pass

    @property
    def x(self):
        return dpg.get_item_pos(self.tag)[0]

    @property
    def y(self):
        return dpg.get_item_pos(self.tag)[1]
