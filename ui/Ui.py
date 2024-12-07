import dearpygui.dearpygui as dpg

from config.SystemConfig import PROHIBITED_BOXES
from config.UiConfig import UiConfig
from utils.ClientLogManager import client_logger
from utils.DataProcessor import ui_data
from utils.Utils import get_all_subclasses
from ui.boxes import *


# class UICallback:
#     def __init__(self):
#         pass
#
#     def on_key_release(self, sender, app_data, user_data):
#         config = user_data
#         if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
#             config.layout.save()
#             client_logger.log("SUCCESS", "Layout saved successfully!")
#         if dpg.is_key_released(dpg.mvKey_F11):
#             dpg.toggle_viewport_fullscreen()
#
#         if dpg.is_key_down(dpg.mvKey_LControl) and dpg.is_key_released(dpg.mvKey_Return):
#             print(123)
#
#     def on_mouse_move(self):
#         ui_data.draw_mouse_pos_last = ui_data.draw_mouse_pos
#         ui_data.draw_mouse_pos = dpg.get_drawing_mouse_pos()
#         ui_data.mouse_move_pos = tuple(
#             x - y for x, y in zip(ui_data.draw_mouse_pos, ui_data.draw_mouse_pos_last)
#         )
#
#     def on_right_click(self, sender, app_data, user_data):
#         pass


class UI:
    def __init__(self):
        self.config = UiConfig()
        self.config.instance = self
        self.console = None
        self.boxes = []
        self.box_count = {}
        self.is_created = False
        self.console_box = None
        self.input_box = None
        # self._ui_callback = UICallback()
        self.all_classes = get_all_subclasses(BaseBox)
        self.generate_add_methods()

    def create(self):
        # 创建主窗口
        self.create_global_handler()
        dpg.create_viewport(title=self.config.title, width=1920, height=1080)
        dpg.configure_app(
            docking=True,
            docking_space=True,
            init_file=self.config.layout.init_file,
            load_init_file=True,
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()
        self.layout_init()
        self.is_created = True

    def layout_init(self):
        # 显示控制台
        # self.console = ConsoleBox(ui=self)
        # self.console.create()
        self.console_box = self.add_ConsoleBox(ui=self)
        self.input_box = self.add_InputConsoleBox(ui=self)
        # 测试界面
        # self.add_NodeBox(ui=self)
        # self.add_MessageBox(ui=self)
        self.add_MessageBox(ui=self)
        self.add_FastLioBox(ui=self)
        # self.add_PointsFaceBox(ui=self)

        
    def show(self):
        if not self.is_created:
            self.create()
        # for box in self.boxes:
        #     if not box.is_created:
        #         box.create()

    def update(self):
        self.show()
        for box in self.boxes:
            if box.is_created:
                box.update()

    def destroy_all_boxes(self):
        for box in self.boxes:
            box.destroy()

    def ui_loop(self):
        self.on_mouse_move()

    def run_loop(self, func=None):
        if func is not None:
            try:
                while dpg.is_dearpygui_running():
                    self.ui_loop()
                    func()
                    dpg.render_dearpygui_frame()
            except Exception as e:
                client_logger.log("ERROR", f"Loop Failed??? {e}")
            finally:
                self.destroy_all_boxes()
        else:
            dpg.start_dearpygui()

    def create_global_handler(self):
        # 创建全局监听
        with dpg.handler_registry() as global_hander:
            dpg.add_key_release_handler(callback=self.on_key_release, user_data=self.config)
        # with dpg.handler_registry():
        #     dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right, callback=self.on_right_click)

    # 生成添加类方法
    def generate_add_methods(self):
        for cls in self.all_classes:
            method_name = f"add_{cls.__name__}"
            # 使用闭包捕获cls
            def add_method(self, cls=cls, **kwargs):
                try:
                    if cls.only and self.box_count.get(cls, 0) >= 1:
                        # 如果盒子已经创建则不重复创建
                        raise Exception("This box can only be created once")
                    instance = cls(**kwargs)
                    instance.create()
                    # self.boxes.append(instance)
                    # self.box_count[cls] = self.box_count.setdefault(cls, 0) + 1
                    # client_logger.log("INFO", f"{instance} instance has been added to the boxes list.")
                    return instance
                except Exception as e:
                    client_logger.log("WARNING", f"Unable to instantiate {cls}", e=e)
            # 将生成的方法绑定到当前实例
            setattr(self, method_name, add_method.__get__(self))

    def on_key_release(self, sender, app_data, user_data):
        config = user_data
        if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
            config.layout.save()
            client_logger.log("SUCCESS", "Layout saved successfully!")
        if dpg.is_key_released(dpg.mvKey_F11):
            dpg.toggle_viewport_fullscreen()
        # if dpg.is_key_down(dpg.mvKey_LControl) and dpg.is_key_released(dpg.mvKey_W):
        #     for box in self.boxes.copy():
        #         if dpg.is_item_focused(box.tag) and box.__class__.__name__ not in PROHIBITED_BOXES:
        #             box.destroy()

        # if dpg.is_key_released(dpg.mvKey_Spacebar):
        #     self.console_box.show()

    def on_mouse_move(self):
        ui_data.draw_mouse_pos_last = ui_data.draw_mouse_pos
        ui_data.draw_mouse_pos = dpg.get_drawing_mouse_pos()
        ui_data.mouse_move_pos = tuple(
            x - y for x, y in zip(ui_data.draw_mouse_pos, ui_data.draw_mouse_pos_last)
        )
