import dearpygui.dearpygui as dpg
from ui.boxes.BaseBox import BaseBox
from ui.components.Canvas2D import Canvas2D
import numpy as np
import utils.python_motion_planning as pmp
from utils.MPCController import MPCController
import math
import time
from api.NewTBKApi import tbk_manager
import pickle
def add_points_to_map_as_circles(points, max_radius):
    obs_circ = []
    for point in points:
        x, y = point  # 提取点的x和y坐标
        r = np.random.randint(1, max_radius + 1)  # 随机生成半径，范围[1, max_radius]
        obs_circ.append([x, y, r])
    return obs_circ


def draw_car(point, color, parent, radius=2):
    pos = point[:2]
    dir = point[2]
    angle = -dir * (180 / math.pi)
    start_angle = 45 + angle
    end_angle = 315 + angle
    # 将角度转换为弧度
    start_radians = np.radians(start_angle)
    end_radians = np.radians(end_angle)
    # 计算每个分段的角度
    angles = np.linspace(start_radians, end_radians, 30 + 1)
    # 计算弧线上的点
    x = pos[0] + radius * np.cos(angles)
    y = pos[1] - radius * np.sin(angles)
    # 将点转换为列表格式
    points = np.column_stack((x, y)).tolist()
    dpg.draw_polygon(points, color=color, fill=color, thickness=2, parent=parent)


class RRTBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas = None
        self.robot_now_pose = [10,10,0]
        self.robot_target_pose = [10,100,0]
        self.obs_circ = []
        self.map = pmp.Map(200, 200)
        self.play_animation = False
        self.path = None
        self.count = 0
        rpm_info = {
            "node_name": "MOTOR_CONTROL",
            "puuid":f"{time.time()}",
            "name": "RPM",
            "msg_name": "RPM",
            "msg_type": "list",
            "tag": self.tag,
        }

        self.suber_rpm = tbk_manager.subscriber(rpm_info, self.set_speed)
        self.mpc = MPCController()
    def set_speed(self,msg):
        data = pickle.loads(msg)
        x, y, w = data
        self.robot_control(x, w)
    def create(self):
        self.points = (np.random.rand(200, 2) * 200).tolist()
        self.obs_circ = add_points_to_map_as_circles(self.points, 4)
        self.map.obs_circ = self.obs_circ
        dpg.configure_item(self.tag, label="CANVAS")
        self.canvas = Canvas2D(self.tag)
        self.main_layer = self.canvas.add_layer()
        self.path_layer = self.canvas.add_layer()
        with self.canvas.draw():
            for point in self.obs_circ:
                dpg.draw_circle(center=point[:2], radius=point[2], color=(255, 255, 255, 255),
                                fill=(255, 255, 255, 255))
        with dpg.handler_registry():
            # dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left,callback=self.add_point,user_data="START")
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left,callback=self.add_point,user_data="END")
            dpg.add_key_release_handler(key=dpg.mvKey_Spacebar,callback=self.path_plan)
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Right,callback=self.set_dir)

    def set_dir(self, sender, app_data):
        mouse_pos = dpg.get_drawing_mouse_pos()
        mouse_pos = tuple(self.canvas.pos_apply_transform(mouse_pos))
        dist_end = np.linalg.norm(np.array(mouse_pos) - np.array(self.robot_target_pose[:2]))
        if dist_end < 10000:
            dir = math.atan2(mouse_pos[1] - self.robot_target_pose[1], mouse_pos[0] - self.robot_target_pose[0])
            dpg.delete_item(self.main_layer, children_only=True)
            self.robot_target_pose[2] = dir
            dpg.delete_item(self.main_layer, children_only=True)
            draw_car(self.robot_now_pose,(0, 255, 0, 255), self.main_layer)
            draw_car(self.robot_target_pose,(0, 0, 255, 255), self.main_layer)

    def add_point(self, sender, app_data, user_data):
        if not dpg.does_item_exist(self.tag):
            return
        if not dpg.is_item_focused(self.tag):
            return
        mouse_pos = dpg.get_drawing_mouse_pos()
        mouse_pos = tuple(self.canvas.pos_apply_transform(mouse_pos))
        # if user_data == "START":
        #     self.start_point[:2] = mouse_pos
        if user_data == "END":
            self.robot_target_pose[:2] = mouse_pos
            dpg.delete_item(self.main_layer, children_only=True)
        draw_car(self.robot_now_pose,(0, 255, 0, 255), self.main_layer)
        draw_car(self.robot_target_pose,(0, 0, 255, 255), self.main_layer)

    def path_plan(self):
        if not dpg.does_item_exist(self.tag):
            return
        if not dpg.is_item_focused(self.tag):
            return
        planner = pmp.RRTConnect(tuple(self.robot_now_pose[:2]), tuple(self.robot_target_pose[:2]), self.map,max_dist=10)
        cost, path, expand = planner.plan()
        dpg.delete_item(self.path_layer, children_only=True)
        dpg.draw_polyline(parent=self.path_layer,points=path, color=(255, 255, 0, 255), thickness=2)
        path = self.mpc.interpolate_path(path)
        self.path = self.mpc.generate_path_with_angles(self.robot_now_pose,self.robot_target_pose,path)
        
        self.t0 = 0
        self.u0 = np.zeros((self.mpc.N, 2))
        self.next_states = np.zeros((self.mpc.N + 1, 3))
        self.next_trajectories, self.next_controls = self.mpc.desired_command_and_trajectory(self.t0, self.robot_now_pose, self.path[0])
        print(self.next_trajectories)

    def robot_control(self, v, omega):
        # 定义噪声参数
        v = v * 0.1
        omega = omega * 0.1
        noise_std_x = 0
        noise_std_y = 0
        noise_std_omega = 0
        # 生成高斯噪声
        noise_x = np.random.normal(0, noise_std_x)
        noise_y = np.random.normal(0, noise_std_y)
        noise_omega = np.random.normal(0, noise_std_omega)

        # 计算当前方向角（以机器人当前角度为基础）
        theta = self.robot_now_pose[2]

        # 根据线速度和方向角计算在x和y方向上的速度分量
        vx = v * np.cos(theta)
        vy = v * np.sin(theta)

        # 加入噪声和角速度影响
        self.robot_now_pose[0] += vx + noise_x
        self.robot_now_pose[1] += vy + noise_y
        self.robot_now_pose[2] += omega + noise_omega

        dpg.delete_item(self.main_layer, children_only=True)
        draw_car(self.robot_now_pose, (0, 255, 0, 255), self.main_layer)
        draw_car(self.robot_target_pose, (0, 0, 255, 255), self.main_layer)

    def update(self):
        if self.path is None:
            return
        if np.linalg.norm(np.array(self.robot_now_pose[:2]) - np.array(self.robot_target_pose[:2])) < 0.5:
            return
        for point in self.path:
            while np.linalg.norm(np.array(self.robot_now_pose[:2]) - np.array(point[:2])) > 5:
                # 调用 MPC 进行一步规划
                self.t0, now_pos, self.u0, self.next_states, u_res, x_m, solve_time = self.mpc.plan(
                    self.t0, self.robot_now_pose, self.u0, self.next_states, self.next_trajectories, self.next_controls
                )
                self.robot_control(u_res[0, 0], u_res[0, 1])
                self.next_trajectories, self.next_controls = self.mpc.desired_command_and_trajectory(self.t0, self.robot_now_pose, point)
                print(f"Current state: {self.u0}, Target point: {point}")
                time.sleep(0.01)
                dpg.render_dearpygui_frame()
        self.path = None
