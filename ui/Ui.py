import dearpygui.dearpygui as dpg
from config.UiConfig import UiConfig
from ui.boxes.ConsoleBox import ConsoleBaseBox
from utils.ClientLogManager import client_logger
from utils.DataProcessor import ui_data
import pickle


class UICallback:
    def __init__(self):
        pass

    def on_key_release(self, sender, app_data, user_data):
        config = user_data
        if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
            config.layout.save()
            client_logger.log("SUCCESS", "Layout saved successfully!")
        if dpg.is_key_released(dpg.mvKey_F11):
            dpg.toggle_viewport_fullscreen()

    def on_mouse_move(self):
        ui_data.draw_mouse_pos_last = ui_data.draw_mouse_pos
        ui_data.draw_mouse_pos = dpg.get_drawing_mouse_pos()
        ui_data.mouse_move_pos = tuple(
            x - y for x, y in zip(ui_data.draw_mouse_pos, ui_data.draw_mouse_pos_last)
        )


class UI:
    def __init__(self):
        self.config = UiConfig()
        self.config.instance = self
        self.console = ConsoleBaseBox()
        self.boxes = self.console.boxes
        self.is_created = False
        self._ui_callback = UICallback()

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
        # 显示控制台
        self.console.create()
        self.is_created = True

    def show(self):
        if not self.is_created:
            self.create()
        for box in self.boxes:
            if not box.is_created:
                box.create()

    def update(self):
        self.show()
        for box in self.boxes:
            box.update()

    def ui_loop(self):
        self._ui_callback.on_mouse_move()

    def run_loop(self, func=None):
        if func is not None:
            while dpg.is_dearpygui_running():
                self.ui_loop()
                func()
                dpg.render_dearpygui_frame()
        else:
            dpg.start_dearpygui()

    def create_global_handler(self):
        # 创建全局监听
        with dpg.handler_registry() as global_hander:
            dpg.add_key_release_handler(callback=self._ui_callback.on_key_release, user_data=self.config)
