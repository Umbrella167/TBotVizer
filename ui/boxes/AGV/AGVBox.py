from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import numpy as np
from api.NewTBKApi import tbk_manager
import pylinalg as la
from math import pi
from matplotlib import cm
import cv2
import time
from utils.ClientLogManager import client_logger

from ui.boxes.AGV.agv_utils import AGVBoxUtils
from ui.boxes.AGV.agv_callback import AGVBoxCallback
from ui.boxes.AGV.agv_param import AGVParam
import utils.planner.python_motion_planning as pmp

class AGVBox(BaseBox):
    only = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas3D = None
        self.count = 0
        self.checkbox_bind = {}
        self.SIZE = AGVParam.CANVAS_SIZE
        self._callback = AGVBoxCallback(self.tag)
        self.geometry = None
        self.is_create_over = False
        self.step = AGVParam.PATH_STEP
        self.step_max_points = AGVParam.MAX_POINTS
        self.arrow = None
        self.arrow_planner = None
        self.last_map_key = (0,0)
        self.subscriber = {}

    def create(self):
        dpg.configure_item(self.tag, height=self.SIZE[1], width=self.SIZE[0])
        self.canvas3D = Canvas3D(self.tag, SIZE=self.SIZE)
        dpg.set_item_drop_callback(self.canvas3D.tag, self._callback.drop_callback)
        self.canvas3D.add(self.lidar_scene())
        self.canvas3D.add(self.create_odometry_path())
        self.canvas3D.add(self.create_planner_path())
        self.canvas3D.add(self.create_arrow())
        self.canvas3D.add(self.create_arrow_planner())

        self.is_create_over = True
        self.map = MapManager(self.canvas3D, self._callback, step=self.step, step_max_points=self.step_max_points)
        self.handler_registry()
        self.auto_subscribe()

    def auto_subscribe(self):
        ep_info_odo = {
            "puuid": time.time(),
            "name": "default",
            "msg_name": "/Odometry",
            "tag": self.tag,
        }
        ep_info_points = {
            "puuid": time.time(),
            "name": "default",
            "msg_name": "/cloud_registered",
            "tag": self.tag,
        }
        self.subscriber[ep_info_odo["msg_name"]] = tbk_manager.subscriber(ep_info_odo, self._callback.odometry_msg)
        self.subscriber[ep_info_points["msg_name"]] = tbk_manager.subscriber(ep_info_points, self._callback.points_msg)

    def create_arrow(self):
        arrow = gfx.Group()
        head = gfx.Mesh(gfx.cylinder_geometry(1.5, 1.55, height=20), gfx.MeshPhongMaterial(color=(1, 1, 0.75, 1)))
        body = gfx.Mesh(gfx.cylinder_geometry(4.0, 0.0, height=10), gfx.MeshPhongMaterial(color=(1, 1, 0.75, 1)))
        head.local.position = (10, 0, 0)
        head.local.rotation = la.quat_from_euler(-np.pi / 2, order="Y")
        body.local.rotation = la.quat_from_euler(-np.pi / 2, order="Y")
        arrow.add(head, body)
        scale = 25
        arrow.local.position = (0, 0, 1000)
        arrow.local.scale = (scale, scale, scale)
        self.arrow = arrow
        return self.arrow

    def create_arrow_planner(self):
        arrow = gfx.Group()
        head = gfx.Mesh(gfx.cylinder_geometry(1.5, 1.55, height=20), gfx.MeshPhongMaterial(color=(0, 0, 0.75, 1)))
        body = gfx.Mesh(gfx.cylinder_geometry(4.0, 0.0, height=10), gfx.MeshPhongMaterial(color=(0, 0, 0.75, 1)))
        head.local.position = (10, 0, 0)
        head.local.rotation = la.quat_from_euler(-np.pi / 2, order="Y")
        body.local.rotation = la.quat_from_euler(-np.pi / 2, order="Y")
        arrow.add(head, body)
        scale = 25
        arrow.local.position = (0, 0, 1000)
        arrow.local.scale = (scale, scale, scale)
        self.arrow_planner = arrow
        return self.arrow_planner

    def handler_registry(self):
        with dpg.handler_registry():
            dpg.add_mouse_drag_handler(
                button=dpg.mvMouseButton_Middle,
                callback=self._callback.publish_target,
                user_data=(self, "drag"),
            )
            dpg.add_mouse_down_handler(
                button=dpg.mvMouseButton_Middle,
                callback=self._callback.publish_target,
                user_data=(self, "down"),
            )
            dpg.add_mouse_release_handler(
                button=dpg.mvMouseButton_Middle,
                callback=self._callback.publish_target,
                user_data=(self, "release"),
            )
            dpg.add_key_down_handler(key=dpg.mvKey_Spacebar, callback=self._callback.move_to_target, user_data="MOVE")
            dpg.add_key_release_handler(
                key=dpg.mvKey_Spacebar, callback=self._callback.move_to_target, user_data="STOP"
            )

    def create_odometry_path(self):
        path = [[0, 0, 0], [0, 0, 0]]
        material = gfx.LineMaterial(thickness=10.0, color=(0.8, 0.7, 0.0, 1.0))
        geometry = gfx.Geometry(positions=path)
        self.line = gfx.Line(geometry, material)
        return self.line

    def create_planner_path(self):
        path = [[0, 0, 0], [0, 0, 0]]
        material = gfx.LineMaterial(thickness=10.0, color=(0, 1, 0.0, 1.0))
        geometry = gfx.Geometry(positions=path)
        self.planner_path = gfx.Line(geometry, material)
        return self.planner_path

    def update_odometry_path(self):
        if not self._callback.path:
            return
        path = AGVBoxUtils.get_path_pos(self._callback.path)
        self.line.geometry.positions = gfx.Buffer(np.array(path, dtype=np.float32))
        self._callback.robot_now_pose = AGVBoxUtils.get_pose(self._callback.odometry)

    def update_planner_path(self, points=None, z=0):
        if not points:
            return

        # Add the z coordinate to each point
        points_with_z = [[x, y, z] for x, y in points]

        # Update the line geometry
        self.planner_path.geometry.positions = gfx.Buffer(np.array(points_with_z, dtype=np.float32))

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
        self.lidar_group.local.scale = (5, 5, 5)
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
        self.lidar_group.local.rotation = [
            odometry["pose"]["orientation"]["x"],
            odometry["pose"]["orientation"]["y"],
            odometry["pose"]["orientation"]["z"],
            odometry["pose"]["orientation"]["w"],
        ]

    def destroy(self):
        super().destroy()

    def update(self):
        if not self.is_create_over:
            return

        if dpg.get_frame_count() % 30 == 0:
            obs_points = self.map.get_points_within_distance(2000)
            path = self._callback.planner_path
            is_collision = AGVBoxUtils.detect_collision(obs_points, path,100)
            if is_collision:
                grid, now_grid_pos, target_grid_pos = self._callback.create_grid()
                self._callback.planner_theta_star()
                client_logger.log("warning","检测到障碍物，重新规划路径")

        self.create_points_could_scene()
        self.update_odometry_path()
        self.update_lidar_pose()
        self.canvas3D.update()

class PointManager:
    def __init__(self, max_points=30000):
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
            self.points = points[-self.max_points :]
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
                self.points[self.current_index :] = points[:end_space]
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
            return self.points[: self.size]
        else:
            return np.roll(self.points, -self.current_index, axis=0)[: self.size]

class MapManager:

    def __init__(self, canvas3D: Canvas3D, callback: AGVBoxCallback, step, step_max_points):
        self.step = step
        self.callback = callback
        self.map = {}  # 使用字典替代列表
        self.step_max_points = step_max_points
        self.gfx_points_size = AGVParam.GFX_POINTS_SIZE
        self.canvas3D = canvas3D

    def get_group_key(self):
        """
        生成分组的唯一标识键
        可以根据需要选择不同的分组策略
        """
        pos = AGVBoxUtils.get_odometry_position(self.callback.odometry)

        # 方法1：基于网格坐标
        grid_x = int(pos[0] // self.step)
        grid_y = int(pos[1] // self.step)
        return (grid_x, grid_y)

        # 方法2：基于圆形区域
        # distance = np.linalg.norm(pos)
        # group_index = int(distance // self.step)
        # return group_index

    def add_points(self, points):
        # 获取当前分组键
        group_key = self.get_group_key()

        # 如果该分组不存在，创建新的分组
        if group_key not in self.map:
            now_points = PointManager(self.step_max_points)
            points_data = {
                "points": now_points,
                "obj": None,
            }
            self.map[group_key] = points_data
             
        # 添加点云数据
        self.map[group_key]["points"].add_points(points)

        # 更新或创建可视化对象
        if self.map[group_key]["obj"] is None:
            self.map[group_key]["obj"] = self.create_gfx_points(self.map[group_key]["points"].get_points)
            self.canvas3D.add(self.map[group_key]["obj"])
        else:
            self.update_gfx_points(self.map[group_key])
    # 调度点云
    def update_gfx_points(self, points_data):
        points = points_data["points"].get_points
        points_data["obj"].geometry.positions = gfx.Buffer(points)

        # 提取 z 轴高度并归一化
        z_values = points[:, 2]  # 提取 z 轴
        normalized_z = (z_values - z_values.min()) / (z_values.max() - z_values.min() + 1e-5)  # 归一化

        # 使用颜色梯度（例如从蓝到绿再到红）
        colormap = cm.get_cmap("jet")  # 'jet' 映射从蓝到红
        colors = colormap(normalized_z)
        colors = colors[:, :4]  # 提取 RGBA 通道

        points_data["obj"].geometry.colors = gfx.Buffer(colors.astype(np.float32))
    # 创建点云
    def create_gfx_points(self, points):
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

    def get_local_grid_points(self, odometry, dist, HIGH_RANGE=AGVParam.HIGH_RANGE_MAP):
        """
        获取指定距离和高度范围内的局部点云网格

        参数:
        - odometry: 当前里程计数据
        - dist: 以当前位置为中心的圆形区域半径
        - HIGH_RANGE: 指定高度范围 [min_z, max_z]

        返回:
        - 局部点云数据 (N x 3 的 NumPy 数组)
        """
        # 获取当前位置
        current_pos = AGVBoxUtils.get_odometry_position(odometry)
        x_center, y_center = current_pos[0], current_pos[1]

        # 计算需要包含的网格范围
        min_grid_x = int((x_center - dist) // self.step)
        max_grid_x = int((x_center + dist) // self.step)
        min_grid_y = int((y_center - dist) // self.step)
        max_grid_y = int((y_center + dist) // self.step)

        # 收集所有网格点云
        local_points = []
        for x in range(min_grid_x, max_grid_x + 1):
            for y in range(min_grid_y, max_grid_y + 1):
                grid_key = (x, y)
                if grid_key in self.map:
                    # 获取该网格的点云
                    grid_points = self.map[grid_key]["points"].get_points

                    # 计算点云到中心点的距离，并筛选高度范围
                    mask = (
                        ((grid_points[:, 0] - x_center) ** 2 + (grid_points[:, 1] - y_center) ** 2) <= dist**2
                    ) & ((grid_points[:, 2] >= HIGH_RANGE[0]) & (grid_points[:, 2] <= HIGH_RANGE[1]))

                    # 筛选符合条件的点
                    filtered_points = grid_points[mask]
                    local_points.append(filtered_points)

        # 合并点云并返回
        if local_points:
            return np.vstack(local_points)  # 一次性合并所有点云
        else:
            return np.empty((0, 3))

    def get_points_within_distance(self, dist):
        """
        获取当前索引下，距离 dist 内的点

        参数:
        - current_index: 当前网格索引 (grid_x, grid_y)
        - dist: 搜索范围的半径

        返回:
        - 满足条件的点云 (N x 3 的 NumPy 数组)
        """
        current_index = self.get_group_key()  
        if current_index not in self.map:
            # 如果当前索引不存在，返回空数组
            return np.empty((0, 3))

        # 获取当前索引内的点云数据
        grid_points = self.map[current_index]["points"].get_points

        # 获取当前网格的中心点
        grid_center_x = current_index[0] * self.step + self.step / 2
        grid_center_y = current_index[1] * self.step + self.step / 2

        # 计算点到中心点的欧几里得距离
        distances = np.sqrt(
            (grid_points[:, 0] - grid_center_x) ** 2 +
            (grid_points[:, 1] - grid_center_y) ** 2 +
            (grid_points[:, 2]) ** 2
        )

        # 筛选出距离小于 dist 的点云
        mask = distances <= dist
        filtered_points = grid_points[mask]

        return filtered_points
