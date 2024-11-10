from cv2.dnn import Layer
from dearpygui import dearpygui as dpg
from tbkpy import _core as tbkpy

from ui.LayoutManager import LayoutConfig, LayoutManager


class CallBack:
    def __init__(self, layout: LayoutManager):
        self._layout_config = layout.config
        self._layout = layout

    def on_key_release(self, sender, app_data):
        if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
            self._layout.save_layout()

    def check_message(self):
        pass
