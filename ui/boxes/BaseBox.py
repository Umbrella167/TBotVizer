from dearpygui import dearpygui as dpg

from utils.ClientLogManager import client_logger

sub_box_x = 300
sub_box_y = 50
pos_offset = 20


class BaseBox(object):
    only = False

    def __init__(self, ui, tag=None, label=None, callback=None):
        self.ui = ui
        self.tag = tag
        self.label = label
        self.callback = callback
        self.is_created = False
        self.only = True
        # self.handler = dpg.add_handler_registry()

    def create(self):
        # 创建
        global sub_box_x, sub_box_y, pos_offset
        if self.is_created:
            client_logger.log("ERROR", "BaseBox has already been created")
            return
        if self.tag:
            dpg.add_window(tag=self.tag, label=self.label, width=800, height=800, pos=(sub_box_x, sub_box_y),
                           on_close=self.destroy)
        else:
            self.tag = dpg.add_window(label=self.label, width=800, height=800, pos=(sub_box_x, sub_box_y),
                                      on_close=self.destroy)
        sub_box_x += pos_offset
        sub_box_y += pos_offset
        self.ui.boxes.append(self)
        self.ui.box_count[self.__class__] = self.ui.box_count.setdefault(self.__class__, 0) + 1
        client_logger.log("INFO", f"{self} instance has been added to the boxes list.")

        self.on_create()

        self.is_created = True

    def on_create(self):
        pass

    def show(self):
        # 显示盒子
        if not dpg.does_item_exist(self.tag):
            self.on_create()
        dpg.show_item(self.tag)

    def hide(self):
        # 隐藏盒子
        dpg.hide_item(self.tag)

    def update(self):
        # raise f"{self.__name__} does not implement update()"
        pass

    def destroy(self):
        # 销毁盒子
        global sub_box_x, sub_box_y, pos_offset
        self.ui.boxes.remove(self)
        self.ui.box_count[self.__class__] -= 1
        dpg.delete_item(self.tag)
        sub_box_x -= pos_offset
        sub_box_y -= pos_offset
        client_logger.log("INFO", f"{self} has been destroyed.")

    @property
    def x(self):
        return dpg.get_item_pos(self.tag)[0]

    @property
    def y(self):
        return dpg.get_item_pos(self.tag)[1]
