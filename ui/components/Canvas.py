import dearpygui.dearpygui as dpg
from contextlib import contextmanager
from ui.boxes import Box

class Transform:
    def __init__(self):
        self.scale = [1, 1, 1]
        self.scale_matrix = dpg.create_scale_matrix(self.scale)
        self.translation = [0, 0, 0]
        self.translation_matrix = dpg.create_translation_matrix(self.translation)
        self.transform = self.translation_matrix * self.scale_matrix
class CanvasCallBack:
    def __init__(self,tranform:Transform):
        self.canvas = None

    def window_resize_callback(self, sender, app_data, user_data):
        width, height, drawlist_tag, drawlist_parent_tag, size_offset = user_data
        parent_width, parent_height = dpg.get_item_rect_size(drawlist_parent_tag)
        if width == -1:
            dpg.configure_item(drawlist_tag, width=parent_width + size_offset[0])
        if height == -1:
            dpg.configure_item(drawlist_tag, height=parent_height + size_offset[1])
    def drag_callback(self, sender, app_data):
        pass
        

class Canvas(Box):
    def __init__(self, parent, size=(-1, -1), size_offset=(0, -50), pos=[]):
        super().__init__()
        self._transform = Transform()
        self._callback = CanvasCallBack(self._transform)
        self.drawlist_tag = None
        self.canvas_tag = None
        self.background_tag = None
        self.drawlist_parent_tag = parent
        self.width, self.height = size
        self.size_offset = size_offset
        self.create(self.drawlist_parent_tag, self.width, self.height, pos)
        self._create_handler()

    def create(self, parent, width=-1, height=-1, pos=[]):
        with dpg.drawlist(
            width=width, height=height, parent=parent, pos=pos
        ) as self.drawlist_tag:
            with dpg.draw_node() as canvas_tag:
                self.canvas_tag = canvas_tag
            with dpg.draw_node() as background_tag:
                self.background_tag = background_tag
        return self.drawlist_tag

    def _create_handler(self, parent=None):
        with dpg.item_handler_registry() as handler:
            dpg.add_item_resize_handler(
                callback=self._callback.window_resize_callback,
                user_data=(
                    self.width,
                    self.height,
                    self.drawlist_tag,
                    self.drawlist_parent_tag,
                    self.size_offset,
                ),
            )
        dpg.bind_item_handler_registry(self.drawlist_parent_tag, handler)



    def add_layer(self, parent=None, tag=None):
        if parent is None:
            parent = self.canvas_tag
        if tag is None:
            tag = dpg.generate_uuid()
        dpg.add_draw_node(parent=self.drawlist_tag, tag=tag)
        return tag

    @contextmanager
    def draw(self, parent=None):
        draw_tag = dpg.generate_uuid()
        if parent is None:
            parent = self.canvas_tag
        with dpg.draw_node(parent=parent) as draw_tag:
            yield draw_tag

