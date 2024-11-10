from dearpygui import dearpygui as dpg
from tbkpy import _core as tbkpy

from ui.Components import DiyComponents
from utils.DataProcessor import UiData

class CallBack:
    def __init__(self, data: UiData, component: DiyComponents):
        self._data = data
        self._layout_manager = self._data.layout_manager
        self._component = component

    def on_key_release(self, sender, app_data):
        if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
            self._layout_manager.save_layout()

    def check_message(self, sender, app_data,user_data):
        msg = user_data[0]
        text_tag = user_data[1]
        def msg_callback(msg):
            if msg:
                print(msg)
        if app_data :
            # suber = tbkpy.Subscriber("puber_test","test_int",msg_callback)
            pass
        else:
            suber = None