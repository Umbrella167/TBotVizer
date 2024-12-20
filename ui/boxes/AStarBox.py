import dearpygui.dearpygui as dpg
from ui.boxes.BaseBox import BaseBox
from ui.components.Canvas2D import Canvas2D
import numpy as np
import utils.python_motion_planning as pmp
from utils.python_motion_planning.utils import Grid

def add_points_to_map_as_circles(points, max_radius):
    """
    将点加入到地图的 obs_circ 中作为圆形障碍物。
    每个点作为圆心，随机生成一个半径。

    Args:
        map_instance: Map类的实例。
        points: 形状为 (N, 2) 的 numpy 数组，每行是一个点 (x, y)。
        max_radius: 圆形障碍物的最大半径。
    """
    obs_circ = []
    for point in points:
        x, y = point  # 提取点的x和y坐标
        r = np.random.randint(1, max_radius + 1)  # 随机生成半径，范围[1, max_radius]
        obs_circ.append([x, y, r])
    return obs_circ
    

class AStarBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas = None
        self.start_point = (10,10)
        self.end_point = (10,100)
        self.obs_circ = []
        self.map = pmp.Map(10000,10000)
    def create(self):
        self.points = (np.random.rand(5000, 2) * 10000).tolist()
        grid_obstacles = set((int(x), int(y)) for x, y in self.points)
        x_range, y_range = 10000, 10000  # 假设网格范围为 10000 x 10000
        self.grid = Grid(x_range, y_range)
        self.grid.update(grid_obstacles)


        self.obs_circ = add_points_to_map_as_circles(self.points, 2)
        self.map.obs_circ = self.obs_circ
        dpg.configure_item(self.tag, label="AStar")
        self.canvas = Canvas2D(self.tag)
        self.main_layer = self.canvas.add_layer()
        self.path_layer = self.canvas.add_layer()
        
        with self.canvas.draw():
            for point in self.obs_circ:
                dpg.draw_circle(center=point[:2], radius=point[2], color=(255, 255, 255, 255),fill=(255, 255, 255, 255))
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left,callback=self.add_point,user_data="START")
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right,callback=self.add_point,user_data="END")

    def add_point(self, sender, app_data, user_data):
        mouse_pos = dpg.get_drawing_mouse_pos()
        mouse_pos = tuple(self.canvas.pos_apply_transform(mouse_pos))
        if user_data == "START":
            self.start_point = mouse_pos
        if user_data == "END":
            self.end_point = mouse_pos
        dpg.delete_item(self.main_layer, children_only=True)
        dpg.draw_circle(parent=self.main_layer,center=self.start_point, radius=3, color=(0, 255, 0, 255),fill=(0, 255, 0, 255))
        dpg.draw_circle(parent=self.main_layer,center=self.end_point, radius=3, color=(0, 0, 255, 255),fill=(0, 0, 255, 255))
        planner = pmp.DStar(self.start_point, self.end_point,self.grid)
        cost, path, expand = planner.plan()

        dpg.delete_item(self.path_layer, children_only=True)
        dpg.draw_polyline(parent=self.path_layer,points=path, color=(255, 255, 0, 255), thickness=2)
    def update(self):
        pass