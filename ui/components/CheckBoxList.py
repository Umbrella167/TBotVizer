import dearpygui.dearpygui as dpg

from ui.components import Component


class CheckBoxList(Component):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.tag:
            dpg.add_window(popup=True, show=False, tag=self.tag)
        else:
            self.tag = dpg.add_window(popup=True, show=False)
        self.create_checkbox_list()

    def create(self):
        pass

    def show(self):
        dpg.configure_item(item=self.tag, pos=(self.parent.x+10, self.parent.y+63))
        dpg.configure_item(item=self.tag, show=True)

    def draw(self):
        self.show()

    def create_checkbox_list(self):
        for l in self.data:
            self.sons.append(dpg.add_checkbox(label=l, parent=self.tag))
