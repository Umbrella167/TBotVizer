from dearpygui import dearpygui as dpg

from static.Params import TypeParams
from ui.LayoutManager import LayoutManager


class CallBack:
    def __init__(self, layout: LayoutManager):
        self._type_params = TypeParams()
        self._layout = layout

    def on_key_release(self, sender, app_data):
        if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
            self._layout.save_layout()

    def check_message(self):
        pass
