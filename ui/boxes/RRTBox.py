import dearpygui.dearpygui as dpg
from ui.boxes.BaseBox import BaseBox  # 假设 BaseBox 是自定义的类
from ui.components.Canvas2D import Canvas2D  # 假设 Canvas2D 是自定义的类
import numpy as np
import utils.planner.python_motion_planning as pmp
import math
import time
from api.NewTBKApi import tbk_manager
import pickle
from utils.planner.local_planner.MPCControllerWithObstacles import MPCController


def add_points_to_map_as_circles(points, max_radius):
    obs_circ = []
    for point in points:
        if np.linalg.norm(np.array(point[:2]) - np.array([10, -10])) < 10:  # 翻转y轴
            continue
        x, y = point  # 提取点的x和y坐标
        y = -y  # 翻转y轴
        r = np.random.randint(1, max_radius + 1)  # 随机生成半径，范围[1, max_radius]
        obs_circ.append([x, y, r])
    return obs_circ


def draw_car(point, color, parent, radius=2):
    pos = [point[0], -point[1]]  # 翻转y轴
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
    y = pos[1] + radius * np.sin(angles)  # 翻转y轴
    # 将点转换为列表格式
    points = np.column_stack((x, y)).tolist()
    dpg.draw_polygon(points, color=color, fill=color, thickness=2, parent=parent)


class RRTBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas = None
        self.robot_now_pose = [100, 100, 2.0]  # 翻转y轴
        self.robot_target_pose = [50, 50.0, 0]  # 翻转y轴
        self.obs_circ = []
        self.map = pmp.Map(-200, 200)
        self.play_animation = False
        self.path = None
        self.count = 0
        rpm_info = {
            "puuid": f"{time.time()}",
            "name": "RPM",
            "msg_name": "RPM",
            "msg_type": "list",
            "tag": self.tag,
        }

        # self.suber_rpm = tbk_manager.subscriber(rpm_info, self.set_speed)

        self.vel_publisher_info = {
            "puuid": "FastLioBox11",
            "name": "MOTOR_CONTROL",
            "msg_name": "RPM",
            "msg_type": "list",
            "tag": self.tag,
        }
        self.vel_publisher = tbk_manager.publisher(self.vel_publisher_info)


        self.mpc = MPCController()

    def set_speed(self, msg):
        data = pickle.loads(msg)
        x, y, w = data
        self.robot_control(x, y, w)

    def create(self):
        self.points = (np.random.rand(300, 2) * 400).tolist()
        self.obs_circ = add_points_to_map_as_circles(self.points, 4)
        self.map.obs_circ = self.obs_circ
        dpg.configure_item(self.tag, label="CANVAS")
        self.canvas = Canvas2D(self.tag)
        self.main_layer = self.canvas.add_layer()
        self.path_layer = self.canvas.add_layer()
        with self.canvas.draw():
            dpg.draw_circle(center=self.robot_target_pose[:2], radius=2, color=(255, 255, 255, 255),
                            fill=(255, 255, 255, 255))
            for point in self.obs_circ:
                dpg.draw_circle(center=point[:2], radius=point[2], color=(255, 255, 255, 255),
                                fill=(255, 255, 255, 255))
        with dpg.handler_registry():
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left, callback=self.add_point, user_data="END")
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Right, callback=self.set_dir)
            dpg.add_key_down_handler(key=dpg.mvKey_Spacebar, callback=self.update_point)

    def set_dir(self, sender, app_data):
        mouse_pos = dpg.get_drawing_mouse_pos()
        mouse_pos = tuple(self.canvas.pos_apply_transform(mouse_pos))
        mouse_pos = [mouse_pos[0], -mouse_pos[1]]  # 翻转y轴
        dist_end = np.linalg.norm(np.array(mouse_pos) - np.array(self.robot_target_pose[:2]))
        if dist_end < 10000:
            dir = math.atan2(mouse_pos[1] - self.robot_target_pose[1], mouse_pos[0] - self.robot_target_pose[0])
            dpg.delete_item(self.main_layer, children_only=True)
            self.robot_target_pose[2] = dir
            dpg.delete_item(self.main_layer, children_only=True)
            draw_car(self.robot_now_pose, (0, 255, 0, 255), self.main_layer)
            draw_car(self.robot_target_pose, (0, 0, 255, 255), self.main_layer)

    def add_point(self, sender, app_data, user_data):
        if not dpg.does_item_exist(self.tag):
            return
        if not dpg.is_item_focused(self.tag):
            return
        mouse_pos = dpg.get_drawing_mouse_pos()
        mouse_pos = tuple(self.canvas.pos_apply_transform(mouse_pos))
        mouse_pos = [mouse_pos[0], -mouse_pos[1]]  # 翻转y轴
        if user_data == "END":
            self.robot_target_pose[:2] = mouse_pos
            dpg.delete_item(self.main_layer, children_only=True)
        draw_car(self.robot_now_pose, (0, 255, 0, 255), self.main_layer)
        draw_car(self.robot_target_pose, (0, 0, 255, 255), self.main_layer)

    def path_plan(self):
        if not dpg.does_item_exist(self.tag):
            return
        if not dpg.is_item_focused(self.tag):
            return
        planner = pmp.RRTConnect(tuple(self.robot_now_pose[:2]), tuple(self.robot_target_pose[:2]), self.map, max_dist=10)
        cost, path, expand = planner.plan()
        path = [[point[0], -point[1]] for point in path]  # 翻转路径点的y轴
        dpg.delete_item(self.path_layer, children_only=True)
        dpg.draw_polyline(parent=self.path_layer, points=path, color=(255, 255, 0, 255), thickness=2)

        self.path = self.mpc.interpolate_path(path)
        self.path = self.mpc.generate_path_with_angles(self.robot_now_pose, self.robot_target_pose, self.path)

    def robot_control(self, vx, vy, omega):
        # 翻转y轴时，vy需要取反
        vx = vx * 0.3
        vy = vy * 0.3  # vy 是前进速度
        omega = omega * 0.3
        noise_std_x = 0.0
        noise_std_y = 0.0
        noise_std_omega = 0.0

        # 生成高斯噪声
        noise_x = np.random.normal(0, noise_std_x)
        noise_y = np.random.normal(0, noise_std_y)
        noise_omega = np.random.normal(0, noise_std_omega)

        # 获取当前方向角（弧度制）
        theta = self.robot_now_pose[2]

        # # 转换到全局坐标系
        # global_vx = vy * np.cos(theta) - vx * np.sin(theta)  # vy 代表前进速度
        # global_vy = -(vy * np.sin(theta) + vx * np.cos(theta))  # 翻转y轴，因此取反

        # 转换到全局坐标系
        global_vx = vy * np.cos(theta) - vx * np.sin(theta)
        global_vy = (vy * np.sin(theta) + vx * np.cos(theta))


        # 更新机器人位置
        self.robot_now_pose[0] += global_vx + noise_x  # 全局坐标系下的 x 方向位移
        self.robot_now_pose[1] += global_vy + noise_y  # 全局坐标系下的 y 方向位移
        self.robot_now_pose[2] += omega + noise_omega  # 更新方向角

        # 绘制机器人位置
        dpg.delete_item(self.main_layer, children_only=True)
        draw_car(self.robot_now_pose, (0, 255, 0, 255), self.main_layer)
        draw_car(self.robot_target_pose, (0, 0, 255, 255), self.main_layer)

    def update_point(self):
        robot_now_pose = [self.robot_now_pose[0],self.robot_now_pose[1], self.robot_now_pose[2]]
        robot_target_pose = [self.robot_target_pose[0], self.robot_target_pose[1], self.robot_target_pose[2]]
        v, s = self.mpc.compute_control(robot_now_pose, robot_target_pose)
        print("s",s)
        self.robot_control(v[0],v[1], v[2])
        self.vel_publisher.publish(pickle.dumps([v[0] * 500,v[1] * 500, v[2] * 8]))
    # def update_path(self):
    #     if self.path is None:
    #         return
    #     for point in self.path:
    #         while np.linalg.norm(np.array(point[:2]) - np.array(self.robot_now_pose[:2])) > 0.5:
    #             v, s = self.mpc.compute_control(self.robot_now_pose, point)
    #             self.robot_control(v[1], -v[0], v[2])
    #             print(v[1], -v[0], v[2])
    #             dpg.render_dearpygui_frame()
    #     self.path = None
