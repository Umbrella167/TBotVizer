import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from ui.components.Canvas2D import Canvas2D
import numpy as np
from utils.Utils import apply_transform,mouse2ssl
from utils.AStart import AStar,generate_grid_from_points
class RRTBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas = None
        self.start_point = [0,0]
        self.end_point = [0,0]
        self.points = []

    def create(self):
        self.points = (np.random.rand(500, 2) * 1000).tolist()
        self.astart_map = generate_grid_from_points(self.points, (1000, 1000))
        print (self.astart_map)
        
        
        
        dpg.configure_item(self.tag, label="CANVAS")
        self.canvas = Canvas2D(self.tag)
        self.main_layer = self.canvas.add_layer()
        self.path_layer = self.canvas.add_layer()
        
        with self.canvas.draw():
            for point in self.points:
                dpg.draw_circle(center=point, radius=3, color=(255, 255, 255, 255),fill=(255, 255, 255, 255))
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left,callback=self.add_point,user_data="START")
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right,callback=self.add_point,user_data="END")
        self.points = np.array(self.points)
        radius = 2
        radii = np.full((self.points.shape[0], 1), radius)  # 创建一个形状为 (n, 1) 的半径数组
        self.points = np.hstack((self.points, radii))

    def add_point(self, sender, app_data, user_data):
        self.canvas.apply_transform(self.main_layer)
        mouse_pos = dpg.get_drawing_mouse_pos()
        # mouse_pos = apply_transform(self.canvas._transform.transform_matrix,mouse_pos)
        # print(self.canvas._transform.translation_matrix)
        # mouse_pos = mouse2ssl(mouse_pos,self.canvas._transform.translation_matrix,self.canvas._transform.scale)
        # dpg.draw_circle(parent=self.main_layer,center=mouse_pos, radius=3, color=(0, 255, 0, 255),fill=(0, 255, 0, 255))
        
        # print(mouse_pos)
        if user_data == "START":
            self.start_point = mouse_pos
        if user_data == "END":
            self.end_point = mouse_pos
        dpg.delete_item(self.main_layer, children_only=True) 
        dpg.draw_circle(parent=self.main_layer,center=self.start_point, radius=3, color=(0, 255, 0, 255),fill=(0, 255, 0, 255))
        dpg.draw_circle(parent=self.main_layer,center=self.end_point, radius=3, color=(0, 0, 255, 255),fill=(0, 0, 255, 255))
        
    def update(self):
        self.a_star = AStar(self.astart_map)
        start = [int(self.start_point[0]),int(self.start_point[1])]
        goal = [int(self.end_point[0]),int(self.end_point[1])]
        path = self.a_star.find_path(start, goal)
        
        if path :
            dpg.delete_item(self.path_layer, children_only=True)
            dpg.draw_polyline(parent=self.path_layer,points=path,color=(255, 255, 0, 255),thickness=2)