from ui.boxes import Box
import dearpygui.dearpygui as dpg
from ui.components.Canvas import Canvas


class CanvasBox(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def create(self):
        self.check_and_create_window()
        # if self.tag:
        #     dpg.add_window(tag=self.tag, label=self.label)
        # else:
        #     self.tag = dpg.add_window(label=self.label)
        if self.label is None:
            dpg.configure_item(self.tag, label="CANVAS")

        self._canvas = Canvas(self.tag)
        with self._canvas.draw():
            dpg.draw_line(p1=[0, 0], p2=[600, 600])
