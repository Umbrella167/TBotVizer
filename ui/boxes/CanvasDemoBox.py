import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from ui.components.Canvas import Canvas


class CanvasDemoBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._canvas = None

    def create(self):
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="CANVAS")

        self._canvas = Canvas(self.tag)
        with self._canvas.draw():
            dpg.draw_line(p1=[0, 0], p2=[600, 600])
