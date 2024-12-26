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
import utils.python_motion_planning as pmp
import time
from utils.MPCController import MPCController
from utils.ClientLogManager import client_logger

@dataclass(frozen=True)
class AGVParam:
    # 一个step内最多的点数
    MAX_POINTS = 18888

    # 每隔PATH_STEP保存一次点云
    PATH_STEP = 1000

    # 点云的单位 * LOCAL_SCALE
    LOCAL_SCALE = 1000

    # 点云大小
    GFX_POINTS_SIZE = 3
    # 保留高度在RANGE内的点
    # HIGH_RANGE_GLOBAL = [-1e9, 1e9]
    HIGH_RANGE_GLOBAL = [-200, 1000]

    HIGH_RANGE_MAP = [-200, 1000]

    # 画布大小
    CANVAS_SIZE = (1920, 1080)

    # 距离阈值(保留 DISTANCE_THRESHOLD% 的点)
    DISTANCE_THRESHOLD = 95

    GRID_SIZE = (-10000, 10000)
    RESOLUTION = 300


class FastLioBoxCallback:

    def __init__(self, tag):
        self.tag = tag
        self.parent = None
        self.points = np.zeros((1, 3), dtype=np.float32)
        self.subscriber = {}
        self.odometry = {}
        # path 走过的路径
        self.path = []
        # 规划的路径
        self.planner_path = []
        # 带有方向的路径
        self.planner_path_pose = []
        self.lidar_scan_area = []
        self.world_mouse_pos = np.array([0, 0, 0], dtype=np.float32)
        self.is_down = False
        self.vel_publisher_info = {
            "puuid": "FastLioBox",
            "name": "MOTOR_CONTROL",
            "msg_name": "RPM",
            "msg_type": "list",
            "tag": self.tag,
        }
        self.vel_publisher = tbk_manager.publisher(self.vel_publisher_info)

        self.allow_mpc_start = True
        self.target_angle = 0
        self.robot_now_pose = [0, 0, 0]
        self.robot_target_pose = [0, 0, 0]
        self.allow_planner = None
        self.mpc = MPCController()
    
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
        points = points[
            (points[:, 2] >= AGVParam.HIGH_RANGE_GLOBAL[0]) & (points[:, 2] <= AGVParam.HIGH_RANGE_GLOBAL[1])
        ]

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
        canvas3D, arrow, map, self.parent, flag, self.arrow_planner = user_data
        self.robot_now_pose = FastLioBoxUtils.get_pose(self.odometry)
        if dpg.does_item_exist(self.tag):
            return
        if not dpg.is_item_focused(canvas3D.tag):
            return
        if flag == "drag":
            direction = self.world_mouse_pos[:2] - canvas3D.get_world_position()[:2]
            print(self.world_mouse_pos[:2] ,canvas3D.get_world_position()[:2])
            norm = np.linalg.norm(direction)
            if norm != 0:  # 避免除以零
                direction = direction / norm
            yaw_angle = np.arctan2(direction[1], direction[0])
            self.target_angle = yaw_angle
            rot = la.quat_from_euler(yaw_angle, order="Z")
            arrow.world.rotation = rot
# 
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
            self.robot_target_pose = taget_pose
            self.planner_theta_star()
            self.mpc_init()
            
    def planner_theta_star(self):
        if self.parent is None:
            return
        time.sleep(1)
        points = self.parent.map.get_local_grid_points(self.odometry, 20000)
        grid = pmp.Grid(points, AGVParam.GRID_SIZE, AGVParam.RESOLUTION)
        # grid.inflate_obstacles(1)
        self.robot_now_pose = FastLioBoxUtils.get_pose(self.odometry)
        now_grid_pos = FastLioBoxUtils.get_point_grid_position(self.robot_now_pose[:2])
        target_grid_pos = FastLioBoxUtils.get_point_grid_position(self.robot_target_pose[:2])
        planner = pmp.ThetaStar(tuple(now_grid_pos), tuple(target_grid_pos), grid)
        cost, self.planner_path, expand = planner.plan()

        img = FastLioBoxUtils.visualize_grid(grid,robot_position=now_grid_pos,path=self.planner_path)
        cv2.imwrite("grid.jpg", img)

        self.planner_path = FastLioBoxUtils.get_real_coordinates(self.planner_path)
        self.planner_path = self.mpc.interpolate_path(self.planner_path, step=5)
        self.planner_path = self.planner_path[::-1]
        self.parent.update_planner_path(self.planner_path)
        return self.planner_path
    
    def mpc_init(self):
        self.allow_mpc_start = True
        self.t0 = 0
        self.u0 = np.zeros((self.mpc.N, 2))
        self.next_states = np.zeros((self.mpc.N + 1, 3))
        self.planner_path_pose = self.mpc.generate_path_with_angles(
            self.robot_now_pose, self.robot_target_pose, self.planner_path
        )
        self.planner_path_pose_index = 0

    def move_to_target(self, sender, app_data, user_data):
        flag = user_data
        if not self.allow_mpc_start:
            return
        if not self.planner_path:
            return
        if not self.odometry:
            return
        if flag == "MOVE":
            self.robot_now_pose = FastLioBoxUtils.get_pose(self.odometry)
            point = self.planner_path_pose[self.planner_path_pose_index]
            point = (point[0], point[1], point[2])
            self.next_trajectories, self.next_controls = self.mpc.desired_command_and_trajectory(
                self.t0, self.robot_now_pose, point
            )
            self.t0, now_pos, self.u0, self.next_states, u_res, x_m, solve_time = self.mpc.plan(
                self.t0, self.robot_now_pose, self.u0, self.next_states, self.next_trajectories, self.next_controls
            )

            self.robot_control(u_res[0, 0], u_res[0, 1])
            print(f"V:{u_res[0, 0]},W: {u_res[0, 1]},NOW_POSE: {self.robot_now_pose},POINT: {point}")


            if np.linalg.norm(np.array(self.robot_now_pose[:2]) - np.array(point[:2])) < 300:
                self.planner_path_pose_index += 1

            if self.planner_path_pose_index >= len(self.planner_path_pose):
                self.allow_mpc_start = False
                self.planner_path = []
                self.planner_path_pose = []
                self.planner_path_pose_index = 0
                self.path = []
                self.path_pos = []
                self.robot_control(0, 0)

                client_logger.log("info", "到达目标点")
            
            rot = la.quat_from_euler(point[2], order="Z")
            self.arrow_planner.world.rotation = rot
            self.arrow_planner.local.position = [point[0], point[1], 0]

        if flag == "STOP":
            self.robot_control(0, 0)

    def robot_control(self, v, omega):
        vy = v * 50
        omega = omega * 0.3
        self.vel_publisher.publish(pickle.dumps([0, -vy, -omega]))


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
                user_data=(self.canvas3D, self.arrow, self.map, self, "drag", self.arrow_planner),
            )
            dpg.add_mouse_down_handler(
                button=dpg.mvMouseButton_Middle,
                callback=self._callback.publish_target,
                user_data=(self.canvas3D, self.arrow, self.map, self, "down", self.arrow_planner),
            )
            dpg.add_mouse_release_handler(
                button=dpg.mvMouseButton_Middle,
                callback=self._callback.publish_target,
                user_data=(
                    self.canvas3D,
                    self.arrow,
                    self.map,
                    self,
                    "release",
                    self.arrow_planner,
                ),
            )
            dpg.add_key_down_handler(key=dpg.mvKey_Spacebar, callback=self._callback.move_to_target, user_data="MOVE")
            dpg.add_key_release_handler(
                key=dpg.mvKey_Spacebar, callback=self._callback.move_to_target, user_data="STOP"
            )

            # dpg.add_key_release_handler(key=dpg.mvKey_Spacebar,callback=self._callback.move_to_target,user_data="STOP")

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
        path = FastLioBoxUtils.get_path_pos(self._callback.path)
        self.line.geometry.positions = gfx.Buffer(np.array(path, dtype=np.float32))
        self._callback.robot_now_pose = FastLioBoxUtils.get_pose(self._callback.odometry)

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
        # self.lidar_group.local.rotation = la.quat_from_euler(
        #     [
        #         odometry["pose"]["orientation"]["x"],
        #         odometry["pose"]["orientation"]["y"],
        #         odometry["pose"]["orientation"]["z"],
        #     ],
        #     order="XYZ",
        # )

    def destroy(self):
        super().destroy()

    def update(self):
        if not self.is_create_over:
            return
        # if self.last_map_key != self.map.get_group_key():
        #     if self._callback.parent is not None:
        #         self._callback.planner_theta_star()
        #     self.last_map_key = self.map.get_group_key()
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
        current_pos = FastLioBoxUtils.get_odometry_position(odometry)
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

class FastLioBoxUtils:
    @staticmethod
    def get_pose(odometry):
        pos = FastLioBoxUtils.get_odometry_position(odometry)
        dir = FastLioBoxUtils.get_odometry_rotation(odometry)
        pose = [pos[0], pos[1], dir]
        return pose

    @staticmethod
    def get_odometry_rotation(odometry):
        if odometry == {}:
            return 0.0  # 如果没有odometry数据，航向角默认为0
        quat = np.array(
            [
                odometry["pose"]["orientation"]["x"],
                odometry["pose"]["orientation"]["y"],
                odometry["pose"]["orientation"]["z"],
                odometry["pose"]["orientation"]["w"],
            ]
        )
        rotation = la.quat_to_euler(quat)
        yaw = rotation[2]  # 提取航向角 (yaw)
        return yaw

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
    def point_cloud_to_grid(points, size=AGVParam.GRID_SIZE, resolution=AGVParam.RESOLUTION):
        # 计算点云的栅格表示
        # 创建栅格
        x_bins = np.arange(size[0], size[1], resolution)
        y_bins = np.arange(size[0], size[1], resolution)

        # 将点分配到栅格
        grid = np.zeros((len(y_bins) - 1, len(x_bins) - 1))

        x_indices = np.digitize(points[:, 0], x_bins) - 1
        y_indices = np.digitize(points[:, 1], y_bins) - 1

        # 处理在范围内的点
        valid_mask = (x_indices >= 0) & (x_indices < grid.shape[1]) & (y_indices >= 0) & (y_indices < grid.shape[0])

        x_indices = x_indices[valid_mask]
        y_indices = y_indices[valid_mask]

        # 可以根据需要选择不同的聚合方法
        # 这里使用简单的二值标记（例如标记为255）

        for x, y in zip(x_indices, y_indices):
            grid[y, x] = 255
        return grid

    @staticmethod
    def get_point_grid_position(point, size=AGVParam.GRID_SIZE, resolution=AGVParam.RESOLUTION):
        """
        计算某个点在网格中的位置

        参数:
        - point: 点的坐标 (x, y)
        - size: 网格的范围 (x_min, x_max)，默认 (-5000, 5000)
        - resolution: 网格分辨率，即每个网格的边长，默认 1

        返回:
        - 网格坐标索引 (x_index, y_index)，如果点不在范围内返回 None
        """
        # 计算网格行列索引
        x_min, x_max = size
        y_min, y_max = size

        x_index = int((point[0] - x_min) // resolution)
        y_index = int((point[1] - y_min) // resolution)

        # 检查点是否在网格范围内
        if x_min <= point[0] < x_max and y_min <= point[1] < y_max:
            return (x_index, y_index)  # 返回网格索引
        else:
            return None  # 如果点不在范围内，返回 None

    @staticmethod
    def points_to_obs_circ(points, radius=1):
        obs_circ = []

        for point in points:
            # 提取点的 x 和 y 坐标
            x, y = point[:2]  # 假设点至少有 x 和 y 坐标（忽略 z 坐标）
            # 添加圆形障碍物 (x, y, radius)
            obs_circ.append((x, y, radius))
        return obs_circ

    @staticmethod
    def get_real_coordinates(grid_positions, size=AGVParam.GRID_SIZE, resolution=AGVParam.RESOLUTION):
        """
        根据网格位置批量返回实际坐标

        参数:
        - grid_positions: 网格坐标索引列表 [(x_index1, y_index1), (x_index2, y_index2), ...]
        - size: 网格的范围 (x_min, x_max)，默认 (-5000, 5000)
        - resolution: 网格分辨率，即每个网格的边长，默认 10

        返回:
        - 实际坐标列表 [(x1, y1), (x2, y2), ...]，对应网格中心的实际坐标
        """
        if not grid_positions:  # 检查输入是否为空
            return []

        x_min, x_max = size
        y_min, y_max = size

        real_coordinates = []
        for grid_position in grid_positions:
            if grid_position is None:
                real_coordinates.append(None)
                continue

            x_index, y_index = grid_position

            # 根据网格索引计算实际坐标
            x = x_min + (x_index + 0.5) * resolution  # 网格中心的 x 坐标
            y = y_min + (y_index + 0.5) * resolution  # 网格中心的 y 坐标

            # 检查是否超出范围
            if x_min <= x < x_max and y_min <= y < y_max:
                real_coordinates.append((x, y))  # 加入实际坐标
            else:
                real_coordinates.append(None)  # 如果超出范围，加入 None

        return real_coordinates

    @staticmethod
    def visualize_grid(grid, cell_size=4, window_name="Grid Map", robot_position=None, path=None):
        """
        使用 OpenCV 可视化 Grid 地图。

        参数:
        - grid: Grid 对象
        - cell_size: 每个网格单元的像素大小
        - window_name: 窗口名称
        - robot_position: (x, y) 形式的元组，表示机器人的当前位置
        - path: 路径信息，为一系列 (x, y) 坐标点的列表，表示机器人移动的路径
        """
        # 获取网格范围
        x_range, y_range = grid.x_range, grid.y_range

        # 创建空白图像
        img_height, img_width = y_range * cell_size, x_range * cell_size
        img = np.ones((img_height, img_width, 3), dtype=np.uint8) * 255  # 白色背景

        # 绘制障碍物
        if grid.obstacles is not None:
            for obs in grid.obstacles:
                x, y = obs
                top_left = (x * cell_size, y * cell_size)
                bottom_right = ((x + 1) * cell_size - 1, (y + 1) * cell_size - 1)
                cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), -1)  # 黑色方块表示障碍物

        # 绘制网格线
        for x in range(0, img_width, cell_size):
            cv2.line(img, (x, 0), (x, img_height), (200, 200, 200), 1)  # 垂直线
        for y in range(0, img_height, cell_size):
            cv2.line(img, (0, y), (img_width, y), (200, 200, 200), 1)  # 水平线

        # 绘制路径信息
        if path is not None and len(path) > 1:
            for i in range(len(path) - 1):
                x1, y1 = path[i]
                x2, y2 = path[i + 1]
                # 转换为图像坐标
                start_point = (int((x1 + 0.5) * cell_size), int((y1 + 0.5) * cell_size))
                end_point = (int((x2 + 0.5) * cell_size), int((y2 + 0.5) * cell_size))
                # 在路径点之间绘制线段
                cv2.line(img, start_point, end_point, (255, 0, 0), 2)  # 蓝色线表示路径

        # 绘制机器人的当前位置
        if robot_position is not None:
            x, y = robot_position
            center = (int((x + 0.5) * cell_size), int((y + 0.5) * cell_size))  # 圆心坐标
            radius = cell_size // 2 - 1  # 圆的半径
            cv2.circle(img, center, radius, (0, 0, 255), -1)  # 红色圆表示机器人

        return img