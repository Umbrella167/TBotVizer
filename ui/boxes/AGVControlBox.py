from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas2D
import pygfx as gfx
import numpy as np
from utils.DataProcessor import tbk_data
import pickle
import pylinalg as la
from math import pi
from matplotlib import cm
from dataclasses import dataclass

@dataclass(frozen=True)
class AGVParam:
    # 一个step内最多的点数
    MAX_POINTS = 5000
    
    # 每隔PATH_STEP保存一次点云
    PATH_STEP = 50
    
    # 点云的单位 * LOCAL_SCALE
    LOCAL_SCALE = 100
    
    # 保留高度在RANGE内的点
    HIGH_RANGE = [0, 200]
    
    #画布大小
    CANVAS_SIZE = (1920, 1080)

class AGVControlBoxCallback:
    def __init__(self, tag):
        self.tag = tag
        self.local_scale = AGVParam.LOCAL_SCALE
        self.points = np.zeros((1, 3), dtype=np.float32)
        self.subscriber = {}
        self.odometry = {}
        self.path = []
        self.lidar_scan_area = []

    def drop_callback(self, sender, app_data):
        ep_info, checkbox_tag = app_data
        ep_info["tag"] = self.tag
        print(ep_info)
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

        # 计算每个点到原点的欧拉距离
        distances = np.linalg.norm(points, axis=1)

        distance_threshold = np.percentile(distances, 85)

        # 保留距离小于等于阈值的点（移除最远的20%点）
        points = points[distances <= distance_threshold]

        # 保留 z 轴在 HIGH_RANGE 范围内的点
        points = points[(points[:, 2] >= AGVParam.HIGH_RANGE[0]) & (points[:, 2] <= AGVParam.HIGH_RANGE[1])]

        # 更新 self.points
        self.points = points

    def odometry_msg(self, msg):
        self.odometry = pickle.loads(msg)
        self.odometry["pose"]["position"]["x"] = self.odometry["pose"]["position"]["x"] * self.local_scale
        self.odometry["pose"]["position"]["y"] = self.odometry["pose"]["position"]["y"] * self.local_scale
        self.odometry["pose"]["position"]["z"] = self.odometry["pose"]["position"]["z"] * self.local_scale
        self.odometr2path(self.odometry)
    def odometr2path(self, odometry, position_threshold=100, orientation_threshold=0.3):
        if not self.path:
            # 如果路径为空，直接添加第一个点
            self.path.append(odometry)
            self.path_pos.append(
                np.array(
                    [
                        odometry["pose"]["position"]["x"],
                        odometry["pose"]["position"]["y"],
                        odometry["pose"]["position"]["z"],
                    ]
                )
            )
            return

        # 当前里程计的位置信息和方向
        pos = np.array(
            [odometry["pose"]["position"]["x"], odometry["pose"]["position"]["y"], odometry["pose"]["position"]["z"]]
        )
        dir = np.array(
            [
                odometry["pose"]["orientation"]["x"],
                odometry["pose"]["orientation"]["y"],
                odometry["pose"]["orientation"]["z"],
                odometry["pose"]["orientation"]["w"],
            ]
        )

        # 上一个路径点的位置信息和方向
        last_pos = np.array(
            [
                self.path[-1]["pose"]["position"]["x"],
                self.path[-1]["pose"]["position"]["y"],
                self.path[-1]["pose"]["position"]["z"],
            ]
        )
        last_dir = np.array(
            [
                self.path[-1]["pose"]["orientation"]["x"],
                self.path[-1]["pose"]["orientation"]["y"],
                self.path[-1]["pose"]["orientation"]["z"],
                self.path[-1]["pose"]["orientation"]["w"],
            ]
        )

        # 计算位移和方向的变化
        position_change = np.linalg.norm(pos - last_pos)  # 欧几里得距离
        distance = int(np.linalg.norm(pos - (0, 0, 0)))
        orientation_change = np.linalg.norm(dir - last_dir)  # 四元数变化的欧几里得距离

        # 如果变化超过阈值，则加入路径
        if position_change > position_threshold or orientation_change > orientation_threshold:
            self.path.append(odometry)



class AGVControlBoxUtils:
    @staticmethod
    def get_odometry_position(odometry):
        if odometry == {}:
            return np.array([0, 0, 0])
        return np.array(
            [
                odometry["pose"]["position"]["x"],
                odometry["pose"]["position"]["y"],
                odometry["pose"]["position"]["z"],
            ]
        )
    @staticmethod
    def get_path_pos(path):
        """
        从路径中提取每个位置点的坐标。

        参数：
            path (list): 包含路径点的列表，每个路径点是一个包含位置信息的字典。

        返回：
            np.ndarray: 一个 N x 3 的数组，其中 N 是路径点的数量,3 是每个点的 x, y, z 坐标。
        """
        if not path:
            return np.array([])  # 如果路径为空，返回空数组

        return np.array([
            [
                point["pose"]["position"]["x"],
                point["pose"]["position"]["y"],
                point["pose"]["position"]["z"]
            ]
            for point in path
        ])

class PointManager:
    def __init__(self,  max_points):
        self.max_points = max_points
        self.points = np.zeros((self.max_points, 3), dtype=np.float32)
        self.current_index = 0  # 用于记录下一个插入的位置
        self.size = 0  # 当前有效点的数量
    def add_points(self, points):
        """添加一批点，如果超出最大长度，则覆盖最早的点"""
        points = np.array(points).reshape(-1, 3)  # 强制转换为二维数组 (N, 3)
        num_new_points = len(points)
        if num_new_points >= self.max_points:
            # 如果输入点数超过缓冲区大小，取最后的 max_points 个点
            self.points = points[-self.max_points:]
            self.current_index = 0
            self.size = self.max_points
        else:
            # 剩余空间
            end_space = self.max_points - self.current_index
            if num_new_points <= end_space:
                # 可以直接插入，不需要分段
                self.points[self.current_index : self.current_index + num_new_points] = points
            else:
                # 需要分段插入
                self.points[self.current_index:] = points[:end_space]
                self.points[: num_new_points - end_space] = points[end_space:]
            # 更新索引和有效点数量
            self.current_index = (self.current_index + num_new_points) % self.max_points
            self.size = min(self.size + num_new_points, self.max_points)



    @property
    def get_points(self):
        """获取所有点(按时间顺序)"""
        if self.size == 0:  # 没有有效点
            return np.empty((0, 3), dtype=np.float32)
        elif self.size < self.max_points:
            return self.points[:self.size]
        else:
            return np.roll(self.points, -self.current_index, axis=0)[:self.size]


class MapManager:
    def __init__(self,canvas:Canvas2D, callback: AGVControlBoxCallback, step, step_max_points):
        self.step = step
        self.callback = callback
        self.map = []
        self.step_max_points = step_max_points
        self.gfx_points_size = 3
        self.all_points = np.empty((0, 3), dtype=np.float32)  # 用于实时维护的全局点集合
        self.canvas = canvas
    def add_points(self, points):
        
        pos = AGVControlBoxUtils.get_odometry_position(self.callback.odometry)
        distance = np.linalg.norm(pos)
        group_index = int(distance // self.step)
        while len(self.map) <= group_index:
            now_points = PointManager(self.step_max_points)
            points_data = {
                "points": now_points,
                "canvas_tag": None,
            }
            self.map.append(points_data)

        self.map[group_index]["points"].add_points(points)
        if self.map[group_index]["canvas_tag"] is None:
            self.map[group_index]["canvas_tag"] = dpg.add_draw_node(parent=self.canvas.canvas_tag)
            self.draw_points(points,self.map[group_index]["canvas_tag"])
        else:
            self.update_points(self.map[group_index])
            # pass/
    def draw_points(self, points,parent):
        for point in points:
            point[1] = -point[1]
            dpg.draw_circle(parent=parent, center=point[:2], radius=2,fill=(255, 0, 0, 255), color=(255, 0, 0, 255))
    def update_points(self, points_data):
        points = points_data["points"].get_points
        canvas_tag = points_data["canvas_tag"]
        dpg.delete_item(canvas_tag, children_only=True)
        self.draw_points(points, canvas_tag)
        
class AGVControlBox(BaseBox):
    only = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas2D = None
        self.count = 0
        self.checkbox_bind = {}
        self.SIZE = AGVParam.CANVAS_SIZE
        self.geometry = None
        self.is_create_over = False
        

    def create(self):
        self._callback = AGVControlBoxCallback(self.tag)
        # dpg.configure_item(self.tag, height=self.SIZE[1], width=self.SIZE[0])
        self.canvas2D = Canvas2D(self.tag,scale_step=0.04)
        self.canvas_lidar = dpg.add_draw_node(parent=self.canvas2D.canvas_tag)
        dpg.set_item_drop_callback(self.canvas2D.group_tag, self._callback.drop_callback)
        self.map = MapManager(self.canvas2D,self._callback, step=AGVParam.PATH_STEP, step_max_points=AGVParam.MAX_POINTS)
        
        self.is_create_over = True
    def draw_lidar(self,pos):
        if self.canvas_lidar is None:
            return
        
        dpg.delete_item(self.canvas_lidar, children_only=True)
        dpg.draw_circle(parent=self.canvas_lidar, center=pos[:2], radius=4,fill=(0, 255, 0, 255), color=(0, 255, 0, 255))
        
    def update_path(self):
        if not self._callback.path:
            return
        pos = AGVControlBoxUtils.get_odometry_position(self._callback.odometry)
        self.draw_lidar(pos)
    def destroy(self):
        super().destroy()

    def update(self):
        if not self.is_create_over:
            return
        if self._callback.points.size < 10:
            return
        self.map.add_points(self._callback.points)

        self.update_path()