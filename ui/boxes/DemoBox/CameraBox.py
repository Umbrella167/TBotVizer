import cv2
import numpy as np
import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from ui.components.TBKManager.TBKManager import tbk_manager
from .proto.python import image_pb2
from ui.components.Canvas2D import Canvas2D


class CameraBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.width = 600
        self.height = 400
        self.img = None
        self.canvas = None
        self.texture_id = None
        self.draw_image = None
        self.tbk_name = None
        self.tbk_msg_name = None
        self.img_suber = None
        tbk_manager.load_module(image_pb2)

    def create(self):
        dpg.configure_item(
            self.tag,
            width=self.width,
            height=self.height,
            no_resize=True,
        )
        # 创建画布
        self.canvas = Canvas2D(
            parent=self.tag,
            auto_mouse_transfrom=False,
            drop_callback=self.drop_callback,
        )
        self.texture_id = self.canvas.texture_register((600, 400), format=dpg.mvFormat_Float_rgb)
        with self.canvas.draw():
            self.draw_image = dpg.draw_image(self.texture_id, pmin=(0, 0), pmax=(600, 400))

    def drop_callback(self, sender, app_data, user_data):
        tbk_manager.unsubscribe(self.tbk_name, self.tbk_msg_name, self.tag)
        self.tbk_name = app_data[0]["name"]
        self.tbk_msg_name = app_data[0]["msg_name"]
        self.img_suber = tbk_manager.subscriber(
            name=self.tbk_name,
            msg_name=self.tbk_msg_name,
            tag=self.tag,
            callback=self.update_img
        )

    def update_img(self, rev_img):
        if rev_img.__class__.__name__ != "Image":
            return
        img_array = np.frombuffer(rev_img.img, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        img = np.array(img, dtype=np.float32)
        dpg.configure_item(self.texture_id, width=img.shape[1], height=img.shape[0])
        dpg.configure_item(self.tag, width=img.shape[1], height=img.shape[0])
        dpg.configure_item(self.draw_image, pmax=(img.shape[1], img.shape[0]))
        self.img = img

    def destroy(self):
        # 销毁之前可以做的事情
        super().destroy()  # 真正销毁Box

    def update(self):
        # 更新图像
        if self.img is not None:
            self.canvas.texture_update(self.texture_id, self.img)
