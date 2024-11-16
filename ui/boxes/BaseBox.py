from dearpygui import dearpygui as dpg

from utils.ClientLogManager import client_logger


class Box(object):
    def __init__(self, tag=None, parent=None, label=None, callback=None):
        self.tag = tag
        self.parent = parent
        self.label = label
        self.callback = callback
        self.is_created = False
        self.only = True

    def check_and_create_window(self):
        if self.is_created:
            client_logger.log("ERROR", "Box has already been created")
            return
        if self.tag:
            dpg.add_window(tag=self.tag, label=self.label,width=800,height=800)
        else:
            self.tag = dpg.add_window(label=self.label,width=800,height=800)
        self.is_created = True

    def create(self):
        # 创建
        self.check_and_create_window()
        raise f"{self.__name__} does not implement create()"

    def show(self):
        if not dpg.does_item_exist(self.tag):
            self.create()

        # raise f"{self.__name__} does not implement draw()"

    def hide(self):
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
