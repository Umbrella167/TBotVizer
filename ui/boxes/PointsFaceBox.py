from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import pylinalg as la
from math import pi
from utils.DataProcessor import MsgSubscriberManager
from utils.ClientLogManager import client_logger
from api.NewTBKApi import tbk_manager
import numpy as np
class PointsFaceBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas3D = None
        self.SIZE = (1920, 1080)

        self.positions = np.array([
            (-1000, -1000, 0),  # 顶点0
            (1000, -1000, 0),   # 顶点1
            (1000, 1000, 0),    # 顶点2
            (-1000, 1000, 0),   # 顶点3
        ], dtype=np.float32)
    def create(self):
        dpg.configure_item(self.tag, label="PointsFaceBox")
        self.canvas3D = Canvas3D(self.tag,self.SIZE)
        self.canvas3D.add(self.scene())

    def scene(self):
        self.plane = gfx.Mesh(
            gfx.Geometry(
                indices=[(0, 1, 2), (2, 3, 0)],  # 定义两个三角形组成一个平面
                positions=[
                    (-1000, -1000, 0),  # 顶点0
                    (1000, -1000, 0),   # 顶点1
                    (1000, 1000, 0),    # 顶点2
                    (-1000, 1000, 0),   # 顶点3
                ],
                colors=[
                    (0, 0, 0, 1),     # 红色
                    (0, 0, 0, 1),     # 绿色
                    (0, 0, 0, 1),     # 蓝色
                    (0, 0, 0, 1),     # 黄色
                ],
            ),
            gfx.MeshBasicMaterial(color_mode="vertex"),
        )
        return self.plane
    def update_face(self):
        
        # Scale the positions by 1.01
        self.positions = self.positions
        self.plane.geometry.positions = gfx.Buffer(self.positions)
        
    def destroy(self):
        self._callback.msg_subscriber_manager.clear()
        super().destroy()

    def update(self):
        if self.plane is None:
            return
        # self.update_face()
        # self.canvas3D.update()
