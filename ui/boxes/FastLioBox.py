from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import numpy as np
from utils.DataProcessor import tbk_data
import pickle
import pylinalg as la
from math import pi
from matplotlib import cm

class FastLioBoxCallback:
    def __init__(self, tag):
        self.tag = tag
        self.max_points = 5000
        self.local_scale = 1000
        self.points = np.zeros((1, 3), dtype=np.float32)
        self.subscriber = {}
        self.odometry = {}
        self.path = []
        self.lidar_scan_area = []
        self.step = 100

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

        # 计算每个点到原点的欧拉距离
        distances = np.linalg.norm(points, axis=1)

        # 找到距离的80%分位点（即20%的最远点的阈值）
        distance_threshold = np.percentile(distances, 85)

        # 保留距离小于等于阈值的点（移除最远的20%点）
        points = points[distances <= distance_threshold]

        # 保留 z 轴在 [0, 200] 范围内的点
        points = points[(points[:, 2] >= 0) & (points[:, 2] <= 200)]

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



class FastLioBoxUtils:
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
    def __init__(self,  max_points = 30000):
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
    def __init__(self,canvas3D:Canvas3D, callback: FastLioBoxCallback,step = 500, step_max_points = 30000):
        self.step = step
        self.callback = callback
        self.map = []
        self.step_max_points = step_max_points
        self.gfx_points_size = 3
        self.canvas3D = canvas3D
    def add_points(self, points):
        
        pos = FastLioBoxUtils.get_odometry_position(self.callback.odometry)
        distance = np.linalg.norm(pos)
        group_index = int(distance // self.step)
        while len(self.map) <= group_index:
            now_points = PointManager(self.step_max_points)
            points_data = {
                "points": now_points,
                "obj": None,
            }
            self.map.append(points_data)

        self.map[group_index]["points"].add_points(points)
        if self.map[group_index]["obj"] is None:
            self.map[group_index]["obj"] = self.create_gfx_points(self.map[group_index]["points"].get_points)
            self.canvas3D.add(self.map[group_index]["obj"])
        else:
            self.update_gfx_points(self.map[group_index])
            # pass/
        
    # 调度点云
    def update_gfx_points(self, points_data):
        points = points_data["points"].get_points
        points_data["obj"].geometry.positions = gfx.Buffer(points)

        # 提取 z 轴高度并归一化
        z_values = points[:, 2]  # 提取 z 轴
        normalized_z = (z_values - z_values.min()) / (z_values.max() - z_values.min() + 1e-5)  # 归一化

        # 使用颜色梯度（例如从蓝到绿再到红）
        colormap = cm.get_cmap('jet')  # 'jet' 映射从蓝到红
        colors = colormap(normalized_z)
        colors = colors[:, :4]  # 提取 RGBA 通道

        points_data["obj"].geometry.colors = gfx.Buffer(colors.astype(np.float32))

    # 创建点云
    def create_gfx_points(self,points):
        size = self.step_max_points
        # 如果 points 的长度小于 size，则补充 [0, 0, 0] 直到长度等于 size
        if len(points) < size:
            points = np.vstack([points, np.zeros((size - len(points), 3))])
        
        points = np.array(points, dtype=np.float32)
        sizes = np.ones(size, dtype=np.float32) * 3
        distances = np.linalg.norm(points, axis=1)  # 计算点到原点的欧拉距离
        normalized_distances = 1 * (distances - distances.min()) / (distances.max() - distances.min() + 1e-5)  # 归一化
        colors = np.zeros((size, 4), dtype=np.float32)
        colors[:, 0] = normalized_distances  # 红色分量根据距离变化
        colors[:, 1] = 1 - normalized_distances  # 绿色分量反向变化
        colors[:, 3] = 1.0  # Alpha 通道设为 1.0（完全不透明）
        self.geometry = gfx.Geometry(
            positions=gfx.Buffer(points),  # 使用 gfx.Buffer 包装 NumPy 数组
            sizes=gfx.Buffer(sizes),  # 包装点大小
            colors=gfx.Buffer(colors),  # 包装点颜色
        )
        material = gfx.PointsMaterial(color_mode="vertex", size_mode="vertex")
        gfx_points = gfx.Points(self.geometry, material)
        return gfx_points
    

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
        self.is_create_over = False
        

    def create(self):
        dpg.configure_item(self.tag, height=self.SIZE[1], width=self.SIZE[0])
        self.canvas3D = Canvas3D(self.tag, SIZE=self.SIZE)
        dpg.set_item_drop_callback(self.canvas3D.tag, self._callback.drop_callback)
        self.canvas3D.add(self.lidar_scene())
        self.canvas3D.add(self.create_path())
        self.is_create_over = True
        self.map = MapManager(self.canvas3D ,self._callback, step=2000, step_max_points=50000)


    def create_path(self):
        path = [[0, 0, 0], [0, 0, 0]]
        material = gfx.LineMaterial(thickness=10.0, color=(0.8, 0.7, 0.0, 1.0))
        geometry = gfx.Geometry(positions=path)
        self.line = gfx.Line(geometry, material)
        return self.line

    def update_path(self):
        if not self._callback.path:
            return
        path = FastLioBoxUtils.get_path_pos(self._callback.path)
        self.line.geometry.positions = gfx.Buffer(np.array(path, dtype=np.float32))

    def create_points_could_scene(self):
        if self._callback.points.size < 10:
            return
        self.map.add_points(self._callback.points)

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
        if not self.is_create_over:
            return
        self.create_points_could_scene()
        self.update_path()
        self.update_lidar_pose()
        self.canvas3D.update()
