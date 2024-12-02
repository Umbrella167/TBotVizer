import dearpygui.dearpygui as dpg

from config.SystemConfig import PROHIBITED_BOXES
from ui.boxes import *

class ConsoleBox(BaseBox):
    only = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fps_text = None
        self.button_tags = []
        self.all_classes = self.ui.all_classes
        self.is_sticky = True
        self.sticky_button = None
        # self.generate_add_methods()


    def on_create(self):
        # 初始化设置
        dpg.configure_item(
            self.tag,
            label="ConsoleBox",
            pos=[0, 0],
            autosize=True,
            # collapsed=False,
            no_resize=True,
            # no_move=True,
            no_collapse=True,
            no_close=True,
            no_background=True,
            # no_saved_settings=True,
            no_title_bar=True,
            popup=not self.is_sticky,
        )
        self.fps_text = dpg.add_text(f"FPS:{dpg.get_frame_rate()}", parent=self.tag)
        # 添加按钮
        width, height, _, data = dpg.load_image(f"static/image/sticky.png")
        with dpg.texture_registry():
            sticky_image = dpg.add_static_texture(width=width, height=height, default_value=data)
        with dpg.group(parent=self.tag):
            self.sticky_button = dpg.add_image_button(
                width=20,
                height=20,
                texture_tag=sticky_image,
                callback=self.sticky,
            )
        # 实例化按钮
        self.generate_add_bottom()

    def key_release_handler(self, sender, app_data, user_data):
        if dpg.is_key_down(dpg.mvKey_LControl) and dpg.is_key_released(dpg.mvKey_Return):
            self.show()
        if dpg.is_key_released(dpg.mvKey_Escape) and not self.is_sticky:
            self.hide()

    # 自动添加按钮
    def generate_add_bottom(self):
        for cls in self.all_classes:
            if cls.__name__ in PROHIBITED_BOXES:
                continue
            instance_func_name = f"add_{cls.__name__}"
            self.button_tags.append(
                dpg.add_button(
                    width=150,
                    label=cls.__name__,
                    parent=self.tag,
                    callback=self.instantiate_box,
                    user_data=instance_func_name,
                )
            )

    def instantiate_box(self, sender, app_data, user_data):
        instance_func_name = user_data
        instance_func = getattr(self.ui, instance_func_name, None)
        # instance_func 中有将新创建的实例添加进 self.boxes
        instance_func(ui=self.ui)

    def sticky(self):
        self.is_sticky = not self.is_sticky
        if self.is_sticky:
            dpg.configure_item(self.tag, popup=False)
        else:
            dpg.configure_item(self.tag, popup=True)

    # # 生成添加类方法
    # def generate_add_methods(self):
    #     for cls in self.all_classes:
    #         if cls == self.__class__:
    #             continue
    #         method_name = f"add_{cls.__name__}"
    #
    #         # 使用闭包捕获cls
    #         def add_method(self, cls=cls, **kwargs):
    #             try:
    #                 if cls.only and self.ui.box_count.get(cls, 0) >= 1:
    #                     # 如果盒子已经创建则不重复创建
    #                     raise Exception("This box can only be created once")
    #                 instance = cls(**kwargs)
    #                 instance.create()
    #                 # self.boxes.append(instance)
    #                 # self.box_count[cls] = self.box_count.setdefault(cls, 0) + 1
    #                 # client_logger.log("INFO", f"{instance} instance has been added to the boxes list.")
    #             except Exception as e:
    #                 client_logger.log("ERROR", f"Unable to instantiate {cls}", e=e)
    #
    #         # 将生成的方法绑定到当前实例
    #         setattr(self, method_name, add_method.__get__(self))

    def update(self):
        dpg.set_value(self.fps_text, f"FPS:{dpg.get_frame_rate()}")
