import dearpygui.dearpygui as dpg

from ui.boxes import *
from utils.ClientLogManager import client_logger

from utils.Utils import get_all_subclasses


class ConsoleBox(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._boxes = []
        self.button_tags = []
        self.all_classes = get_all_subclasses(Box)
        self.generate_add_methods()

    def create(self):
        # 初始化设置
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="ConsoleBox")
        dpg.configure_item(
            self.tag,
            pos=[0, 0],
            height=1000,
            autosize=True,
            menubar=True,
            collapsed=False,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_close=True,
            no_saved_settings=True,
            no_title_bar=True,
        )
        # 实例化按钮
        self.generate_add_bottom()

    def generate_add_bottom(self):
        for cls in self.all_classes:
            if cls == self.__class__:
                continue
            instance_func_name = f"add_{cls.__name__}"
            self.button_tags.append(
                dpg.add_button(
                    label=instance_func_name,
                    parent=self.tag,
                    callback=self.callback_manager,
                    user_data=instance_func_name,
                )
            )

    def callback_manager(self, sender, app_data, user_data):
        instance_func_name = user_data
        instance_func = getattr(self, instance_func_name, None)
        # instance_func 中有将新创建的实例添加进 self.boxes
        instance_func()

    def generate_add_methods(self):
        for cls in self.all_classes:
            if cls == self.__class__:
                continue
            method_name = f"add_{cls.__name__}"
            # 使用闭包捕获cls
            def add_method(self, cls=cls, **kwargs):
                try:
                    instance = cls(**kwargs)
                    self.boxes.append(instance)
                    client_logger.log("SUCCESS", f"{cls} 实例已添加到 boxes 列表中。")
                except TypeError as e:
                    client_logger.log("ERROR", f"无法实例化 {cls}：{e}")
            # 将生成的方法绑定到当前实例
            setattr(self, method_name, add_method.__get__(self))

    @property
    def boxes(self):
        return self._boxes
