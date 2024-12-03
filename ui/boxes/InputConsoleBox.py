import dearpygui.dearpygui as dpg

from config.SystemConfig import PROHIBITED_BOXES
from ui.boxes import *


class InputConsoleBox(BaseBox):
    only = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.width = 1000
        self.height = 300
        self.is_sticky = False
        self.all_class_name = [i.__name__ for i in self.ui.all_classes if i.__name__ not in PROHIBITED_BOXES]
        self.input_text = None
        self.select_index = 0
        self.filter_set = None
        self.filter_list = self.all_class_name
        self.selectables = {}

    def on_create(self):
        # 初始化设置
        if self.label is None:
            dpg.configure_item(self.tag, label="InputConsoleBox")

        dpg.configure_item(
            self.tag,
            width=self.width,
            height=self.height,
            # autosize=True,
            # collapsed=False,
            # no_resize=True,
            no_move=True,
            no_collapse=True,
            no_close=True,
            no_saved_settings=True,
            no_title_bar=True,
            popup=not self.is_sticky,
            show=False,
        )
        self.input_text = dpg.add_input_text(
            width=self.width, height=self.height, callback=self.filter_res, parent=self.tag
        )
        for cls_name in self.all_class_name:
            self.selectables[cls_name] = dpg.add_selectable(
                label=cls_name, filter_key=cls_name, parent=self.tag, callback=None
            )

    def filter_res(self, sender, app_data):
        self.select_index = 0
        [dpg.hide_item(i) for i in self.selectables.values()]
        self.filter_list = []
        for cls_name in self.all_class_name:
            pos = 0
            match = True
            for char in app_data.lower():
                pos = cls_name.lower().find(char, pos)
                if pos == -1:
                    match = False
                    break
                pos += 1
            if match:
                dpg.show_item(self.selectables[cls_name])
                self.filter_list.append(cls_name)

    def key_release_handler(self, sender, app_data, user_data):

        key = app_data
        if not dpg.is_item_visible(self.tag) and key == dpg.mvKey_Spacebar:
            dpg.set_item_pos(
                self.tag,
                [dpg.get_viewport_width() / 2 - self.width / 2, dpg.get_viewport_height() / 2 - self.height / 2],
            )
            dpg.configure_item(self.input_text, default_value="")
            self.filter_res(None, "")
            self.show()
        if key == dpg.mvKey_Escape and not self.is_sticky:
            self.hide()
        if self.filter_list:
            cls_name = self.filter_list[self.select_index]
            if dpg.is_item_visible(self.tag) and key == dpg.mvKey_Return:
                func_name = f"add_{cls_name}"
                self.instantiate_box(func_name)
 
        dpg.focus_item(self.input_text)

    def key_press_handler(self, sender, app_data, user_data):
        key = app_data
        if self.filter_list:
            for selectable in self.selectables.values():
                dpg.configure_item(selectable, default_value=False)
            if key == dpg.mvKey_Up:
                self.select_index -= 1
                if self.select_index < 0:
                    self.select_index = len(self.filter_list) - 1
            if key == dpg.mvKey_Down:
                self.select_index += 1
                if self.select_index == len(self.filter_list):
                    self.select_index = 0
            cls_name = self.filter_list[self.select_index]
            dpg.configure_item(self.selectables[cls_name], default_value=True)
            dpg.configure_item(self.input_text, hint=cls_name)

        dpg.focus_item(self.input_text)

    def instantiate_box(self, func_name):
        instance_func_name = func_name
        instance_func = getattr(self.ui, instance_func_name, None)
        # instance_func 中有将新创建的实例添加进 self.boxes
        instance_func(ui=self.ui)

    def destroy(self):
        dpg.delete_item(self.handler)
        super().destroy()
