from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import numpy as np
from utils.DataProcessor import tbk_data
import pickle
import pylinalg as la
from math import pi


class PointManager:
    def __init__(self, max_points):
        self.max_points = max_points
        self.points = np.zeros((self.max_points, 3), dtype=np.float32)
        self.current_index = 0  # 用于记录下一个插入的位置

    def add_points(self, points):
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
            return np.vstack((self.points[self.current_index :], self.points[: self.current_index]))


class FastLioBoxCallback:
    def __init__(self, tag):
        self.tag = tag
        self.max_points = 5000
        self.local_scale = 1000
        self.points = np.zeros((1, 3), dtype=np.float32)
        self.subscriber = {}
        self.odometry = {}
        self.map = PointManager(self.max_points * 100)

    def drop_callback(self, sender, app_data):
        ep_info, checkbox_tag = app_data
        ep_info["tag"] = self.tag
        if ep_info["msg_type"] == "sensor_msgs/PointCloud2":
            if ep_info["msg_name"] not in self.subscriber:
                self.subscriber[ep_info["msg_name"]] = tbk_data.Subscriber(ep_info, self.points_msg)
        if ep_info["msg_type"] == "nav_msgs/Odometry":
            if ep_info["msg_name"] not in self.subscriber:
                self.subscriber[ep_info["msg_name"]] = tbk_data.Subscriber(ep_info, self.odometry_msg)

    def points_msg(self, msg):
        # 反序列化点云数据
        points = pickle.loads(msg)
        
        # 对点云进行缩放
        points = points * self.local_scale
        
        # 转换为 NumPy 数组
        points = np.array(points, dtype=int)

        # 保留 (x, y, z) 坐标均能被 2 整除的点
        # 假设 points 的形状为 (N, 3)，其中 N 是点数
        divisible_by_2 = np.all((points % 5 == 0), axis=1)
        filtered_points = points[divisible_by_2]
        
        # 栅格化：将保留的点转换为整数并降低精度
        self.points = np.array(filtered_points, dtype=np.float32)

    def odometry_msg(self, msg):
        self.odometry = pickle.loads(msg)
        self.odometry["pose"]["position"]["x"] = self.odometry["pose"]["position"]["x"] * self.local_scale
        self.odometry["pose"]["position"]["y"] = self.odometry["pose"]["position"]["y"] * self.local_scale
        self.odometry["pose"]["position"]["z"] = self.odometry["pose"]["position"]["z"] * self.local_scale


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
        self.canvas3D.add(self.lidar_scene())

    # def check_point(self, points):
    #     # 获取 tbk_map 中的点
    #     tbk_map = self._callback.map.get_points  # 假设返回一个点云数组，形状为 (M, 3)
        
    #     # 转换为集合，便于快速查找
    #     tbk_map_set = {tuple(point) for point in tbk_map}
        
    #     # 找到 points 中不在 tbk_map 中的点
    #     unique_points = [point for point in points if tuple(point) not in tbk_map_set]
    #     self._callback.map.add_points(unique_points)
    #     # 返回结果
    #     return np.array(unique_points)
    def create_points_could_scene(self):

        if self._callback.points.size < 10:
            return
        
        # points = self.check_point(self._callback.points)
        points = self._callback.points

        length = len(points)
        distances = np.linalg.norm(points, axis=1)  # 计算点到原点的欧拉距离
        normalized_distances = 2 * (distances - distances.min()) / (distances.max() - distances.min() + 1e-5)  # 归一化
        colors = np.zeros((length, 4), dtype=np.float32)
        colors[:, 0] = normalized_distances  # 红色分量根据距离变化
        colors[:, 1] = 1 - normalized_distances  # 绿色分量反向变化
        colors[:, 3] = 1.0  # Alpha 通道设为 1.0（完全不透明）
        size = len(points)
        sizes = np.ones(size, dtype=np.float32) * 3

        self.geometry = gfx.Geometry(
            positions=gfx.Buffer(points),  # 使用 gfx.Buffer 包装 NumPy 数组
            sizes=gfx.Buffer(sizes),  # 包装点大小
            colors=gfx.Buffer(colors),  # 包装点颜色
        )
        material = gfx.PointsMaterial(color_mode="vertex", size_mode="vertex")
        points = gfx.Points(self.geometry, material)
        self.canvas3D.add(points)
        return points

    def lidar_scene(self):
        self.grid = gfx.GridHelper(5000, 50, color1="#444444", color2="#222222")
        self.lidar_group = gfx.Group()
        self.lidar_meshes = gfx.load_mesh("static/model/mid360.STL")[0]
        rot = la.quat_from_euler([-pi / 2, 0, -pi], order="XYZ")
        self.lidar_meshes.local.rotation = rot
        self.AxesHelper = gfx.AxesHelper(150, 2)
        self.lidar_group.add(self.lidar_meshes, self.AxesHelper)
        return self.lidar_group

    def update_lidar_pose(self):
        if self._callback.odometry == {}:
            return
        odometry = self._callback.odometry
        self.lidar_group.local.position = (
            odometry["pose"]["position"]["x"],
            odometry["pose"]["position"]["y"],
            odometry["pose"]["position"]["z"],
        )
        self.lidar_group.local.rotation = la.quat_from_euler(
            [
                odometry["pose"]["orientation"]["x"],
                odometry["pose"]["orientation"]["y"],
                odometry["pose"]["orientation"]["z"],
            ],
            order="XYZ",
        )

    def destroy(self):
        super().destroy()

    def update(self):
        self.create_points_could_scene()
        if self.lidar_group:
            self.update_lidar_pose()
        self.canvas3D.update()