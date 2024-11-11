import dearpygui.dearpygui as dpg

from config import SystemConfig
from ui.LayoutManager import LayoutManager
from utils.CallBack import CallBack


class UI:
    def __init__(self, layout: LayoutManager, boxes: list):
        # self.config =
        self._boxes = boxes
        self._Layout = layout
        self._callback = CallBack(layout)

    def show(self):
        self.create_global_handler()
        dpg.configure_app(
            docking=True,
            docking_space=True,
            init_file=self._Layout.init_file,
            load_init_file=True,
        )
        dpg.create_viewport(title="TBK-ParamManager", width=1920, height=1080)
        # 原show_ui部分
        self._Layout.load_layout()
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def create_global_handler(self):
        with dpg.handler_registry() as global_hander:
            dpg.add_key_release_handler(callback=self._callback.on_key_release)

    def run_loop(self, func=None):
        if func is not None:
            while dpg.is_dearpygui_running():
                func()
                dpg.render_dearpygui_frame()
        else:
            dpg.start_dearpygui()

    def draw(self):
        for box in self._boxes:
            box.draw()
        # 直接显示
        self.show()

    def update(self):
        for box in self._boxes:
            box.update()

    @property
    def Layout(self):
        return self._Layout
