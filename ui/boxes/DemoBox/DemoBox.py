import time
import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from ui.boxes.BaseBox import BaseBox
from ui.components.TBKManager.TBKManager import tbk_manager
from .proto.python import actor_info_pb2
from .proto.python import imu_info_pb2
from .proto.python import jointstate_info_pb2
from .proto.python import image_pb2
from ui.components.Canvas2D import Canvas2D
from ...components.TBKManager.ParamData import ParamData


class DemoBox(BaseBox):
    # only = True 表示只能创建一个实例
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input = None
        self.suber = None
        self.puber = None
        tbk_manager.load_module(actor_info_pb2)
        tbk_manager.load_module(imu_info_pb2)
        tbk_manager.load_module(jointstate_info_pb2)
        tbk_manager.load_module(image_pb2)
        self.img = None

        self.test_param = ParamData(prefix="test_path", name="test_name")

        a = ParamData(prefix="box1/module1", name="pos")

        self.test_param2 = ParamData(prefix="test_path", name="test_name")
        self.test_param.value = "10"

    def create(self):
        # create 会自动创建dpg窗口， 窗口拥有tag，获取的方法是 self.tag
        self.input = dpg.add_input_text(parent=self.tag, default_value=self.data.tolist())
        self.puber = tbk_manager.publisher(name="name", msg_name="msg_name", msg_type=tbk_manager.all_types.ByteMultiArray)
        self.suber = tbk_manager.subscriber(name="name", msg_name="msg_name", tag=self.tag, callback=lambda m: dpg.set_value(item=self.input, value=m))
        self.imgsuber = tbk_manager.subscriber(name="tz_agv", msg_name="tz_agv_free_camera_image", tag=self.tag, callback=self.update_img)
        # 创建按钮
        dpg.add_button(label="test", parent=self.tag, callback=lambda: self.puber.publish(f"test{time.time()}"))
        # 创建画布
        self.canvas = Canvas2D(self.tag, auto_mouse_transfrom=False)
        self.texture_id = self.canvas.texture_register((600, 400), format=dpg.mvFormat_Float_rgb)
        with self.canvas.draw():
            dpg.draw_image(self.texture_id, pmin=(0, 0), pmax=(600, 400))

    def update_img(self, rev_img):
        img_array = np.frombuffer(rev_img.img, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.array(img, dtype=np.float32)

        self.img = img
        # cv2.imwrite("img.jpg", img)

    def destroy(self):
        # 销毁之前可以做的事情
        super().destroy()  # 真正销毁Box

    def update(self):
        # 更新图像
        if self.img is not None:
            self.canvas.texture_update(self.texture_id, self.img)

        self.test_param.value = str(int(self.test_param.value) + 1)
        # self.test_param2.value = str(int(self.test_param2.value) - 1)
