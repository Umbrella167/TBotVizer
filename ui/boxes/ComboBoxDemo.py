from ui.boxes import Box
import dearpygui.dearpygui as dpg

from ui.components.CheckBoxList import CheckBoxList


class ComboBoxDemo(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create()

    def create(self):
        if self.tag:
            dpg.add_window(tag=self.tag)
        else:
            self.tag = dpg.add_window()
        dpg.add_button(label="Options     V", callback=self.on_click, parent=self.tag)
        self.sons.append(CheckBoxList(tag="options_window" ,parent=self, data=self.data))
        return self.tag

    def draw(self):
        # self.create()
        pass

    def update(self):
        pass

    def on_click(self, sender, app_data):
        for son in self.sons:
            son.draw()
