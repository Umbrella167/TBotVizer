from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas2D import Canvas2D


class CanvasDemoBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._canvas = None

    def create(self):
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="CANVAS")
        with dpg.group(drop_callback=lambda:print(1),parent=self.tag) as a :
            self._canvas = Canvas2D(a,auto_mouse_transfrom=False)
        with self._canvas.draw():
            dpg.draw_line(p1=[0, 0], p2=[600, 600])