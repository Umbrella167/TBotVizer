import dearpygui.dearpygui as dpg
from ui.boxes.BaseBox import BaseBox
from ui.components.Canvas2D import Canvas2D
import numpy as np
import utils.python_motion_planning as pmp
import utils.MPCPlanner as mpc
import math
def add_points_to_map_as_circles(points, max_radius):
    obs_circ = []
    for point in points:
        x, y = point  # 提取点的x和y坐标
        r = np.random.randint(1, max_radius + 1)  # 随机生成半径，范围[1, max_radius]
        obs_circ.append([x, y, r])
    return obs_circ

def draw_car(point, color, parent,radius = 2):
    pos = point[:2]
    dir = point[2]
    angle =  -dir * (180 / math.pi)
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
    dpg.draw_polygon(points, color=color, fill=color,thickness=2,parent=parent)

class RRTBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas = None
        self.start_point = [10,10,0]
        self.end_point = [10,100,0]
        self.obs_circ = []
        self.map = pmp.Map(200,200)
        self.play_animation = False
        self.planned_trajectory = []
        self.planned_trajectory_index = 0
        self.path = []
    def create(self):
        self.points = (np.random.rand(200, 2) * 200).tolist()
        self.obs_circ = add_points_to_map_as_circles(self.points, 2)
        self.map.obs_circ = self.obs_circ
        dpg.configure_item(self.tag, label="CANVAS")
        self.canvas = Canvas2D(self.tag)
        self.main_layer = self.canvas.add_layer()
        self.path_layer = self.canvas.add_layer()
        
        with self.canvas.draw():
            for point in self.obs_circ:
                dpg.draw_circle(center=point[:2], radius=point[2], color=(255, 255, 255, 255),fill=(255, 255, 255, 255))
        with dpg.handler_registry():
            # dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left,callback=self.add_point,user_data="START")
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left,callback=self.add_point,user_data="END")
            dpg.add_key_release_handler(key=dpg.mvKey_Spacebar,callback=self.path_plan)
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Right,callback=self.set_dir)
    def set_dir(self, sender, app_data):
        mouse_pos = dpg.get_drawing_mouse_pos()
        mouse_pos = tuple(self.canvas.pos_apply_transform(mouse_pos))
        dist_end = np.linalg.norm(np.array(mouse_pos) - np.array(self.end_point[:2]))
        if dist_end < 10000:
            dir = math.atan2(mouse_pos[1] - self.end_point[1], mouse_pos[0] - self.end_point[0])
            dpg.delete_item(self.main_layer, children_only=True)
            self.end_point[2] = dir
            dpg.delete_item(self.main_layer, children_only=True)
            draw_car(self.start_point,(0, 255, 0, 255), self.main_layer)
            draw_car(self.end_point,(0, 0, 255, 255), self.main_layer)

    def add_point(self, sender, app_data, user_data):
        mouse_pos = dpg.get_drawing_mouse_pos()
        mouse_pos = tuple(self.canvas.pos_apply_transform(mouse_pos))
        # if user_data == "START":
        #     self.start_point[:2] = mouse_pos
        if user_data == "END":
            self.end_point[:2] = mouse_pos
        dpg.delete_item(self.main_layer, children_only=True)
        draw_car(self.start_point,(0, 255, 0, 255), self.main_layer)
        draw_car(self.end_point,(0, 0, 255, 255), self.main_layer)

    def path_plan(self):
        planner = pmp.RRTConnect(tuple(self.start_point[:2]), tuple(self.end_point[:2]), self.map,max_dist=1)
        cost, path, expand = planner.plan()
        dpg.delete_item(self.path_layer, children_only=True)
        dpg.draw_polyline(parent=self.path_layer,points=path, color=(255, 255, 0, 255), thickness=2)
        self.path = path
        self.mpc_planner = mpc.MPCPlanner()
        self.planned_trajectory = self.mpc_planner.plan(tuple(self.start_point), tuple(self.end_point), self.path)
        self.planned_trajectory_index = 0
        self.play_animation = True
        

    
    def update(self):
        
        if self.play_animation :
            dpg.delete_item(self.main_layer, children_only=True)
            self.start_point = self.planned_trajectory[1]
            draw_car(self.start_point,(0, 255, 0, 255), self.main_layer)
            draw_car(self.end_point,(0, 0, 255, 255), self.main_layer)
            self.planned_trajectory = self.mpc_planner.plan(tuple(self.start_point), tuple(self.end_point), self.path)
            if np.linalg.norm(np.array(self.start_point[:2]) - np.array(self.end_point[:2])) < 10:
                self.play_animation = False