
import dearpygui.dearpygui as dpg
import numpy as np
from api.NewTBKApi import tbk_manager
import pickle
import pylinalg as la
import cv2
import utils.planner.python_motion_planning as pmp
from utils.planner.local_planner.MPCController import MPCController
from utils.ClientLogManager import client_logger
from ui.boxes.AGV.agv_param import AGVParam
from ui.boxes.AGV.agv_utils import AGVBoxUtils

class AGVBoxCallback:

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
        self.parent,flag = user_data
        canvas3D = self.parent.canvas3D
        arrow = self.parent.arrow
        map = self.parent.map
        self.arrow_planner = self.parent.arrow_planner

        self.robot_now_pose = AGVBoxUtils.get_pose(self.odometry)
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
            rot = la.quat_from_euler(yaw_angle, order="Z")
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
            self.robot_target_pose = taget_pose
            self.planner_theta_star()
            self.mpc_init()

    def create_grid(self):
        points = self.parent.map.get_local_grid_points(self.odometry, 20000)
        grid = pmp.Grid(points, AGVParam.GRID_SIZE, AGVParam.RESOLUTION)
        self.robot_now_pose = AGVBoxUtils.get_pose(self.odometry)
        now_grid_pos = AGVBoxUtils.get_point_grid_position(self.robot_now_pose[:2])
        target_grid_pos = AGVBoxUtils.get_point_grid_position(self.robot_target_pose[:2])
        return grid, now_grid_pos, target_grid_pos
    
    def planner_theta_star(self):
        if self.parent is None:
            return
        grid, now_grid_pos, target_grid_pos = self.create_grid()
        planner = pmp.ThetaStar(tuple(now_grid_pos), tuple(target_grid_pos), grid)
        cost, self.planner_path, expand = planner.plan()
        cv2.imwrite("grid.jpg", AGVBoxUtils.visualize_grid(grid,robot_position=now_grid_pos,path=self.planner_path))

        self.planner_path = AGVBoxUtils.get_real_coordinates(self.planner_path)
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
            self.robot_now_pose = AGVBoxUtils.get_pose(self.odometry)
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

    def is_path_reachable(self):
        grid, now_grid_pos, target_grid_pos = self.create_grid()
        res = AGVBoxUtils.is_path_reachable(grid, self.planner_path)
        return res


        