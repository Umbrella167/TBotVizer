import dearpygui.dearpygui as dpg

from api.PygfxApi import GfxEngine
from ui.boxes.BaseBox import BaseBox
from ui.components.Canvas import Canvas
from utils.Utils import new_texture


class IMU3DBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gfx_engine = GfxEngine(size=(800, 600), pixel_ratio=1, max_fps=999)
        self.canvas = None
        self.texture_tag = None
        self.imu_world = None
        self.count = 0

    def create(self):
        self.check_and_create_window()
        self.imu_world = self.gfx_engine.new_world()
        self.imu_world.load_background("static/image/Heartbeat.png")
        self.imu_world.add_plane()
        image = self.imu_world.draw_image()
        # print(image.shape)
        self.texture_tag = new_texture(image)
        if self.label is None:
            dpg.configure_item(self.tag, label="IMU3DBox")
        self.canvas = Canvas(parent=self.tag)
        with self.canvas.draw():
            dpg.draw_image(self.texture_tag, pmin=[0, 0], pmax=[800, 600])

    def update(self):
        dpg.set_value(self.texture_tag, self.imu_world.draw())
        self.count += 0.05
        self.position = [0, 0, self.count]
        self.imu_world.camera.local.position = self.position
