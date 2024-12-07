from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import numpy as np
from tbkpy.socket.udp import UDPMultiCastReceiver
import struct
import numpy as np

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


class PointsGetter:
    def __init__(self):
        self.point_data_port_ = UDPMultiCastReceiver(
            "233.233.233.233", 56301, callback=lambda msg: self.update_points(msg, "points")
        )
        # self.imu_data_port = UDPMultiCastReceiver(
        #     "233.233.233.233", 56401, callback=lambda msg: self.update_points(msg, "imu_data")
        # )
        self.points = []
        self.points_around = []
        self.count = 0
    def parse_point_data(self, data):
        # 跳过前36字节,直接解包为结构化数组
        dtype = np.dtype(
            [
                ("x", "<i4"),  # int32, little-endian
                ("y", "<i4"),
                ("z", "<i4"),
                ("reflectivity", "u1"),  # uint8
                ("tag", "u1"),  # uint8
            ]
        )
        point_array = np.frombuffer(data[36:], dtype=dtype)

        # 提取 x, y, z 坐标以及 tag
        
        points = np.column_stack((point_array["x"], point_array["y"], point_array["z"], point_array["tag"]))
        return points

    def filter_points(self, points):
        """
        过滤掉置信度低的点(TAG的bit 4~5 表示置信度)。
        置信度判断规则:
        - 高置信度:bit 4~5 = 00
        - 中置信度:bit 4~5 = 01
        - 低置信度:bit 4~5 = 10 (会被过滤掉)
        """
        filtered_points = []
        for point in points:
            tag = point[3]  # TAG 值在第 4 列
            confidence_bits = (tag & 0b00110000)  # 提取 TAG 的 bit 4~5
            if confidence_bits == 0b00000000 or confidence_bits == 0b00010000:  # 高或中置信度
                filtered_points.append(point[:3])  # 只保留 x, y, z

        return np.array(filtered_points)

    def update_points(self, msg, sender):
        self.count += 1
        if sender == "imu_data":
            imu_data = msg[0]
            imu_payload = imu_data[28:]  # 跳过前28字节的头部
            gyro_x, gyro_y, gyro_z, acc_x, acc_y, acc_z = struct.unpack("<ffffff", imu_payload[:24])

        if sender == "points":
            point_data = msg[0]
            points = self.parse_point_data(point_data)
            if len(points) == 0:
                return

            # 过滤掉置信度低的点
            points = self.filter_points(points)
            self.points_around.append(points)
            if len(self.points_around) > 208:
                self.points = np.vstack(self.points_around)
                self.points_around = []
                self.count = 0

class PointsCouldBox(BaseBox):
    only = True
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas3D = None
        self.count = 0
        self.checkbox_bind = {}
        self.SIZE = (1920, 1080)
        self.points_getter = PointsGetter()
        # 一圈的点: 208 * 96,  
        self.max_points = 208 * 96 * 5
        self.points_manager = PointManager(self.max_points)
        #np.zeros((self.max_points, 3), dtype=np.float32)
        self.geometry = None
    def on_create(self):
        if self.label is None:
            dpg.configure_item(self.tag, label="IMU3DBox")
        dpg.configure_item(self.tag, height=self.SIZE[1], width=self.SIZE[0])
        self.canvas3D = Canvas3D(self.tag, SIZE=self.SIZE)
        self.canvas3D.add(self.create_points_could_scene())

    def update_points(self):
        if len(self.points_getter.points) == 0:  # 使用 size 判断数组是否为空
            return
        self.points_manager.add_point(self.points_getter.points)

        if self.geometry is not None:
            # 更新点的位置数据
            updated_positions = self.points_manager.get_points
            self.geometry.positions = gfx.Buffer(updated_positions)

            # 根据欧拉距离动态设置颜色
            # 欧拉距离 = sqrt(x^2 + y^2 + z^2)
            distances = np.linalg.norm(updated_positions, axis=1)  # 计算点到原点的欧拉距离
            normalized_distances = 2 * (distances - distances.min()) / (distances.max() - distances.min() + 1e-5)  # 归一化
            
            # 设置颜色为 RGBA 格式
            colors = np.zeros((self.max_points, 4), dtype=np.float32)
            colors[:, 0] = normalized_distances  # 红色分量根据距离变化
            colors[:, 1] = 1 - normalized_distances  # 绿色分量反向变化
            colors[:, 3] = 1.0  # Alpha 通道设为 1.0（完全不透明）

            self.geometry.colors = gfx.Buffer(colors)  # 更新颜色缓冲区

    def create_points_could_scene(self):
        
        sizes = np.ones(self.max_points, dtype=np.float32) * 3
        colors = np.ones((self.max_points, 4), dtype=np.float32)
        self.geometry = gfx.Geometry(
            positions=gfx.Buffer(self.points_manager.get_points),  # 使用 gfx.Buffer 包装 NumPy 数组
            sizes=gfx.Buffer(sizes),  # 包装点大小
            colors=gfx.Buffer(colors),  # 包装点颜色
        )
        material = gfx.PointsMaterial(color_mode="vertex", size_mode="vertex")
        points = gfx.Points(self.geometry, material)
        return points

    def destroy(self):
        super().destroy()
        
    def update(self):
        positions_group = self.update_points()
        self.canvas3D.update()
        if positions_group is not None:
            self.canvas3D.remove(positions_group)
