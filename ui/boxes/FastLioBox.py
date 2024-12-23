from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import numpy as np
from api.NewTBKApi import tbk_manager
import pickle
import pylinalg as la
from math import pi
from matplotlib import cm
from dataclasses import dataclass
import cv2
@dataclass(frozen=True)
class AGVParam:
    # 一个step内最多的点数
    MAX_POINTS = 10000

    # 每隔PATH_STEP保存一次点云
    PATH_STEP = 200

    # 点云的单位 * LOCAL_SCALE
    LOCAL_SCALE = 1000

    GFX_POINTS_SIZE = 3
    # 保留高度在RANGE内的点
    HIGH_RANGE = [0, 500]

    # 画布大小
    CANVAS_SIZE = (1920, 1080)

    DISTANCE_THRESHOLD = 85


class FastLioBoxCallback:

    def __init__(self, tag):
        self.tag = tag
        self.points = np.zeros((1, 3), dtype=np.float32)
        self.subscriber = {}
        self.odometry = {}
        self.path = []
        self.lidar_scan_area = []
        self.world_mouse_pos = np.array([0, 0, 0], dtype=np.float32)
        self.is_down = False 
        self.target_publish_info = {
            "puuid": "FastLioBox",
            "name": "target",
            "msg_name": "target",
            "msg_type": "list",
            "tag": self.tag,
        }
        # self.target_publish = tbk_manager.publisher(self.target_publish_info)
        self.target_angle = 0
   
    def drop_callback(self, sender, app_data):
        ep_info, checkbox_tag = app_data
        ep_info["tag"] = self.tag
        if ep_info["msg_type"] == "sensor_msgs/PointCloud2":
            if ep_info["msg_name"] not in self.subscriber:
                self.subscriber[ep_info["msg_name"]] = tbk_manager.subscriber(ep_info, self.points_msg)
        if ep_info["msg_type"] == "nav_msgs/Odometry":
            if ep_info["msg_name"] not in self.subscriber:
                self.subscriber[ep_info["msg_name"]] = tbk_manager.subscriber(ep_info, self.odometry_msg)

    def points_msg(self, msg):
        # 反序列化点云数据
        points = pickle.loads(msg)
        # 对点云进行缩放
        points = points * AGVParam.LOCAL_SCALE

        # 计算每个点到原点的欧拉距离
        distances = np.linalg.norm(points, axis=1)

        # 找到距离的80%分位点（即20%的最远点的阈值）
        distance_threshold = np.percentile(distances, AGVParam.DISTANCE_THRESHOLD)

        # 保留距离小于等于阈值的点（移除最远的20%点）
        points = points[distances <= distance_threshold]

        # 保留 z 轴在 [0, 200] 范围内的点
        points = points[(points[:, 2] >= AGVParam.HIGH_RANGE[0]) & (points[:, 2] <= AGVParam.HIGH_RANGE[1])]

        # 更新 self.points
        self.points = points

    def odometry_msg(self, msg):
        self.odometry = pickle.loads(msg)
        self.odometry["pose"]["position"]["x"] = self.odometry["pose"]["position"]["x"] * AGVParam.LOCAL_SCALE
        self.odometry["pose"]["position"]["y"] = self.odometry["pose"]["position"]["y"] * AGVParam.LOCAL_SCALE
        self.odometry["pose"]["position"]["z"] = self.odometry["pose"]["position"]["z"] * AGVParam.LOCAL_SCALE
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
     
    def publish_target(self, sender, app_data, user_data):
        canvas3D,arrow,map,flag = user_data
        
        if dpg.does_item_exist(self.tag):
            return
        if not dpg.is_item_focused(canvas3D.tag):
            return
        if flag == "drag":
            direction = self.world_mouse_pos[:2] - canvas3D.get_world_position()[:2]
            norm = np.linalg.norm(direction)
            if norm != 0:  # 避免除以零
                direction = direction / norm
            yaw_angle = np.arctan2(direction[1], direction[0])
            self.target_angle = yaw_angle
            rot = la.quat_from_euler([np.pi / 2,yaw_angle - np.pi / 2], order="XY")
            arrow.world.rotation = rot
        if flag == "down":
            if self.is_down:
                return
            self.world_mouse_pos = canvas3D.get_world_position()
            arrow.local.position = self.world_mouse_pos
            self.is_down = True
        if flag == "release":
            self.is_down = False
            taget_pose = self.world_mouse_pos
            taget_pose[2] = self.target_angle
            points = map.get_local_grid_points(self.odometry, 1000)
            grid = FastLioBoxUtils.point_cloud_to_grid(points)
            cv2.imwrite("grid.jpg", grid)
            print(grid.shape)

class FastLioBox(BaseBox):
    only = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas3D = None
        self.count = 0
        self.checkbox_bind = {}
        self.SIZE = AGVParam.CANVAS_SIZE
        self._callback = FastLioBoxCallback(self.tag)
        self.geometry = None
        self.is_create_over = False
        self.step = AGVParam.PATH_STEP
        self.step_max_points = AGVParam.MAX_POINTS
        self.arrow = None
        
    def create(self):
        dpg.configure_item(self.tag, height=self.SIZE[1], width=self.SIZE[0])
        self.canvas3D = Canvas3D(self.tag, SIZE=self.SIZE)
        dpg.set_item_drop_callback(self.canvas3D.tag, self._callback.drop_callback)
        self.canvas3D.add(self.lidar_scene())
        self.canvas3D.add(self.create_path())
        self.canvas3D.add(self.create_arrow())
        self.is_create_over = True
        self.map = MapManager(self.canvas3D, self._callback, step=self.step, step_max_points=self.step_max_points)
        self.handler_registry()

    def create_arrow(self):
        arrow = gfx.Group()
        arrow_data = [((0, 0, -10), (1, 1, 0.75, 1), gfx.cylinder_geometry(1.5, 1.5, height=20)),
        ((0, 0, 5), (1, 1, 0.75, 1), gfx.cylinder_geometry(4, 0.0, height=10))]
        for pos, color, geometry in arrow_data:
            material = gfx.MeshPhongMaterial(color=color)
            wobject = gfx.Mesh(geometry, material)
            wobject.local.position = pos
            arrow.add(wobject)

        scale = 25
        arrow.local.position = (0, 0, 1000)
        arrow.local.scale = (scale, scale, scale)
        # arrow.local.rotation = la.quat_from_euler(np.pi/2, order="Z")
        self.arrow = arrow
        return self.arrow
    
    def handler_registry(self):
        with dpg.handler_registry():
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Middle,callback=self._callback.publish_target,user_data=(self.canvas3D,self.arrow,self.map,"drag"))
            dpg.add_mouse_down_handler(button=dpg.mvMouseButton_Middle,callback=self._callback.publish_target,user_data=(self.canvas3D,self.arrow,self.map,"down"))
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Middle,callback=self._callback.publish_target,user_data=(self.canvas3D,self.arrow,self.map,"release"))

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

    def __init__(self, canvas3D: Canvas3D, callback: FastLioBoxCallback, step, step_max_points):
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
        pos = FastLioBoxUtils.get_odometry_position(self.callback.odometry)

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

    def get_local_grid_points(self, odometry, dist):
        """
        获取指定距离内的局部点云网格

        参数:
        - odometry: 当前里程计数据
        - dist: 以当前位置为中心的圆形区域半径

        返回:
        - 局部点云数据
        """
        # 获取当前位置
        current_pos = FastLioBoxUtils.get_odometry_position(odometry)
        x_center, y_center = current_pos[0], current_pos[1]

        # 计算需要包含的网格范围
        min_grid_x = int((x_center - dist) // self.step)
        max_grid_x = int((x_center + dist) // self.step)
        min_grid_y = int((y_center - dist) // self.step)
        max_grid_y = int((y_center + dist) // self.step)

        # 收集局部点云数据
        local_points = []
        for x in range(min_grid_x, max_grid_x + 1):
            for y in range(min_grid_y, max_grid_y + 1):
                grid_key = (x, y)
                if grid_key in self.map:
                    # 获取该网格的点云
                    grid_points = self.map[grid_key]["points"].get_points

                    # 计算点云到中心点的距离
                    point_distances = np.sqrt(
                        ((grid_points[:, 0] - x_center) ** 2) + 
                        ((grid_points[:, 1] - y_center) ** 2)
                    )

                    # 过滤在指定距离内的点云
                    mask = point_distances <= dist
                    filtered_points = grid_points[mask]
                    
                    if len(filtered_points) > 0:
                        local_points.append(filtered_points)

        # 合并点云
        if local_points:
            return np.vstack(local_points)
        else:
            return np.empty((0, 3))

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

        return np.array(
            [
                [point["pose"]["position"]["x"], point["pose"]["position"]["y"], point["pose"]["position"]["z"]]
                for point in path
            ]
        )

    @staticmethod
    def point_cloud_to_grid(points, x_range=(-500, 500), y_range=(-500, 500), resolution=1):
        # 创建栅格
        x_bins = np.arange(x_range[0], x_range[1], resolution)
        y_bins = np.arange(y_range[0], y_range[1], resolution)

        # 将点分配到栅格
        grid = np.zeros((len(y_bins) - 1, len(x_bins) - 1))

        x_indices = np.digitize(points[:, 0], x_bins) - 1
        y_indices = np.digitize(points[:, 1], y_bins) - 1

        # 处理在范围内的点
        valid_mask = (x_indices >= 0) & (x_indices < grid.shape[1]) & (y_indices >= 0) & (y_indices < grid.shape[0])

        x_indices = x_indices[valid_mask]
        y_indices = y_indices[valid_mask]

        # 可以根据需要选择不同的聚合方法
        # 这里使用高度的最大值

        # heights = points[valid_mask, 2]
        # for x, y, h in zip(x_indices, y_indices, heights):
        #     grid[y, x] = max(grid[y, x], h)

        for x, y in zip(x_indices, y_indices):
            grid[y, x] = 255
        return grid