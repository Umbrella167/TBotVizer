import dearpygui.dearpygui as dpg
from ui.components import Component


class Canvas():
    def __init__(self):
        pass
    def create(self,parent):
        with dpg.drawlist(width=800, height=800,parent=parent) as self.drawlist_tag:
            pass

    # def show(self):
    #     pass