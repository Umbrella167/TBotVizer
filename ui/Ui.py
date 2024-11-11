import dearpygui.dearpygui as dpg

from config.SystemConfig import config
from config.UiConfig import UiConfig


class UI:
    def __init__(self, config: UiConfig):
        self.config = config

    def show(self):
        self.create_global_handler()
        dpg.create_viewport(title=self.config.title, width=1920, height=1080)
        dpg.configure_app(
            docking=True,
            docking_space=True,
            init_file=self.config.layout.init_file,
            load_init_file=True,
        )
        # 原show_ui部分
        # self.config.layout.load()
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def create_global_handler(self):
        with dpg.handler_registry() as global_hander:
            dpg.add_key_release_handler(callback=self.on_key_release)

    def on_key_release(self, sender, app_data):
        if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
            print("布局保存成功")
            self.config.layout.save()

    def run_loop(self, func=None):
        if func is not None:
            while dpg.is_dearpygui_running():
                func()
                dpg.render_dearpygui_frame()
        else:
            dpg.start_dearpygui()

    def draw(self):
        for box in self.config.boxes:
            box.draw()

    def update(self):
        for box in self.config.boxes:
            box.update()
