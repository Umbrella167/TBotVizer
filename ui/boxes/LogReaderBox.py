
from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from utils.Utils import item_auto_resize


class LogReaderBaseBox(BaseBox):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._canvas = None

    def create(self):
        self.check_and_create_window()
        with dpg.child_window(parent=self.tag,width=-1) as self.logreader_child_window_tag:
            dpg.add_text("Log Reader:")
            dpg.add_button(label="Open File")
            dpg.add_slider_double()
        item_auto_resize(self.msg_child_window_tag,self.tag,0.618)