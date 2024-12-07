from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import numpy as np
from utils.DataProcessor import tbk_data
from utils.DataProcessor import ui_data

import pickle 
import pylinalg as la
from math import pi
from utils.Utils import ScreenToWorldPoint

class PointManager:
    def __init__(self, max_points):
        self.max_points = max_points
        self.points = np.zeros((self.max_points, 3), dtype=np.float32)
        self.current_index = 0  # 用于记录下一个插入的位置

    def add_point(self, points):
        """添加一批点,如果超出最大长度,则覆盖最早的点"""
        points = np.array(points).reshape(-1, 3)  # 强制转换为二维数组 (N, 3)

        for point in points:
            self.points[self.current_index] = point
            self.current_index = (self.current_index + 1) % self.max_points  # 循环覆盖

    @property
    def get_points(self):
        """获取所有点(按时间顺序)"""
        if self.current_index == 0:
            return self.points
        else:
            return np.vstack((self.points[self.current_index:], self.points[:self.current_index]))

class FastLioBoxCallback:
    def __init__(self,tag):
        self.tag = tag
        self.max_points = 50000
        self.local_scale = 1000
        self.points_manager = PointManager(self.max_points)
        self.subscriber = {}
        self.odometry = {}
    def drop_callback(self,sender, app_data):
        ep_info,checkbox_tag = app_data
        ep_info["tag"] = self.tag
        if ep_info["msg_type"] == "sensor_msgs/PointCloud2":
            if ep_info["msg_name"] not in self.subscriber:
                self.subscriber[ep_info["msg_name"]] = tbk_data.Subscriber(ep_info, self.points_msg)
        if ep_info["msg_type"] == "nav_msgs/Odometry":
            if ep_info["msg_name"] not in self.subscriber:
                self.subscriber[ep_info["msg_name"]] = tbk_data.Subscriber(ep_info, self.odometry_msg)
    def points_msg(self,msg):
        points = pickle.loads(msg)
        points = points * self.local_scale
        self.points_manager.add_point(points)
    def odometry_msg(self,msg):
        self.odometry = pickle.loads(msg)
        self.odometry['pose']['position']['x'] = self.odometry['pose']['position']['x'] * self.local_scale
        self.odometry['pose']['position']['y'] = self.odometry['pose']['position']['y'] * self.local_scale
        self.odometry['pose']['position']['z'] = self.odometry['pose']['position']['z'] * self.local_scale
class FastLioBox(BaseBox):
    only = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas3D = None
        self.count = 0
        self.checkbox_bind = {}
        self.SIZE = (1920, 1080)
        self._callback = FastLioBoxCallback(self.tag)
        self.geometry = None
    def on_create(self):
        dpg.configure_item(self.tag, height=self.SIZE[1], width=self.SIZE[0])
        self.canvas3D = Canvas3D(self.tag, SIZE=self.SIZE)
        dpg.set_item_drop_callback(self.canvas3D.tag, self._callback.drop_callback)
        self.canvas3D.add(self.create_points_could_scene())
        self.canvas3D.add(self.lidar_scene())

        self.cube = gfx.Mesh(
            gfx.box_geometry(width=1000, height=1000, depth=1000, width_segments=1000, height_segments=1000, depth_segments=1000),
            gfx.MeshBasicMaterial(color=[1,1,1,1], flat_shading=False),
        )
        self.cube.local.position = (0, 0, 0)
        self.canvas3D.add(self.cube)
    def update_lidar_pose(self):
        if self._callback.odometry == {}:
            return
        odometry = self._callback.odometry
        self.lidar_group.local.position = (odometry["pose"]["position"]["x"], odometry["pose"]["position"]["y"], odometry["pose"]["position"]["z"])
        self.lidar_group.local.rotation = la.quat_from_euler([odometry["pose"]["orientation"]["x"], odometry["pose"]["orientation"]["y"], odometry["pose"]["orientation"]["z"]],order='XYZ')

    def update_points(self):
        if len(self._callback.points_manager.get_points) == 0:  # 使用 size 判断数组是否为空
            return
        if self.geometry is not None:
            # 更新点的位置数据
            updated_positions = self._callback.points_manager.get_points
            self.geometry.positions = gfx.Buffer(updated_positions)
            # 根据欧拉距离动态设置颜色
            # 欧拉距离 = sqrt(x^2 + y^2 + z^2)
            distances = np.linalg.norm(updated_positions, axis=1)  # 计算点到原点的欧拉距离
            normalized_distances = 2 * (distances - distances.min()) / (distances.max() - distances.min() + 1e-5)  # 归一化
            
            # 设置颜色为 RGBA 格式
            colors = np.zeros((self._callback.max_points, 4), dtype=np.float32)
            colors[:, 0] = normalized_distances  # 红色分量根据距离变化
            colors[:, 1] = 1 - normalized_distances  # 绿色分量反向变化
            colors[:, 3] = 1.0  # Alpha 通道设为 1.0（完全不透明）

            self.geometry.colors = gfx.Buffer(colors)  # 更新颜色缓冲区
    def lidar_scene(self):
        self.grid = gfx.GridHelper(5000, 50, color1="#444444", color2="#222222")
        self.lidar_group = gfx.Group()
        self.lidar_meshes = gfx.load_mesh("static/model/mid360.STL")[0]
        rot = la.quat_from_euler([-pi / 2, 0, -pi],order='XYZ')
        self.lidar_meshes.local.rotation = rot
        self.AxesHelper = gfx.AxesHelper(150, 2)
        # self.lidar_meshes.local.scale_x = 20
        # self.lidar_meshes.local.scale_y = 20
        # self.lidar_meshes.local.scale_z = 20
        self.lidar_group.add(self.lidar_meshes, self.AxesHelper)
        return self.lidar_group
    def create_points_could_scene(self):
        
        sizes = np.ones(self._callback.max_points, dtype=np.float32) * 3
        colors = np.ones((self._callback.max_points, 4), dtype=np.float32)
        self.geometry = gfx.Geometry(
            positions=gfx.Buffer(self._callback.points_manager.get_points),  # 使用 gfx.Buffer 包装 NumPy 数组
            sizes=gfx.Buffer(sizes),  # 包装点大小
            colors=gfx.Buffer(colors),  # 包装点颜色
        )
        material = gfx.PointsMaterial(color_mode="vertex", size_mode="vertex")
        points = gfx.Points(self.geometry, material)
        return points

    def destroy(self):
        super().destroy()
        
    def update(self):
        # print(ScreenToWorldPoint(ui_data.draw_mouse_pos, self.canvas3D.camera,self.canvas3D.viewport))
        # self.cube.local.position = ScreenToWorldPoint(ui_data.draw_mouse_pos, self.canvas3D.camera,self.canvas3D.viewport)
        positions_group = self.update_points()
        if self.lidar_group:
            self.update_lidar_pose()
        self.canvas3D.update()
        if positions_group is not None:
            self.canvas3D.remove(positions_group)
