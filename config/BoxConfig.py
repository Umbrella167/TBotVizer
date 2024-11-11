from typing import List
import dearpygui.dearpygui as dpg

from config import BaseConfig
from ui.components import Component


class BoxConfig(BaseConfig):
    def __init__(self, data=None, components: List[Component]=None):
        super().__init__()
        self.data = data
        self.components = components
