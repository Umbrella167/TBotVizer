from dearpygui import dearpygui as dpg

from utils.ClientLogManager import client_logger

sub_box_x = 300
sub_box_y = 50
pos_offset = 20


class Box(object):
    only = False

    def __init__(self, tag=None, parent=None, label=None, callback=None):
        self.tag = tag
        self.parent = parent
        self.label = label
        self.callback = callback
        self.is_created = False
        self.only = True

    def check_and_create_window(self):
        global sub_box_x, sub_box_y, pos_offset
        if self.is_created:
            client_logger.log("ERROR", "Box has already been created")
            return
        if self.tag:
            dpg.add_window(tag=self.tag, label=self.label, width=800, height=800, pos=(sub_box_x, sub_box_y),
                           on_close=self.destroy)
        else:
            self.tag = dpg.add_window(label=self.label, width=800, height=800, pos=(sub_box_x, sub_box_y),
                                      on_close=self.destroy)
        sub_box_x += pos_offset
        sub_box_y += pos_offset
        self.is_created = True

    def create(self):
        # 创建
        self.check_and_create_window()
        raise f"{self.__name__} does not implement create()"

    def show(self):
        # 显示盒子
        if not dpg.does_item_exist(self.tag):
            self.create()
        dpg.show_item(self.tag)

    def hide(self):
        # 隐藏盒子
        dpg.hide_item(self.tag)
        pass

    def update(self):
        # raise f"{self.__name__} does not implement update()"
        pass

    def destroy(self):
        # 销毁盒子
        global sub_box_x, sub_box_y, pos_offset
        self.parent.boxes.remove(self)
        self.parent.box_count[self.__class__] -= 1
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
