"""
@file: env.py
@breif: 2-dimension environment
@author: Winter
@update: 2023.1.13
"""
from math import sqrt
from abc import ABC, abstractmethod
from scipy.spatial import cKDTree
import numpy as np

from .node import Node

class Env(ABC):
    """
    Class for building 2-d workspace of robots.

    Parameters:
        x_range (int): x-axis range of enviroment
        y_range (int): y-axis range of environmet
        eps (float): tolerance for float comparison

    Examples:
        >>> from utils.python_motion_planning.utils import Env
        >>> env = Env(30, 40)
    """
    def __init__(self, x_range: int, y_range: int, eps: float = 1e-6) -> None:
        # size of environment
        self.x_range = x_range  
        self.y_range = y_range
        self.eps = eps

    @property
    def grid_map(self) -> set:
        return {(i, j) for i in range(self.x_range) for j in range(self.y_range)}

    @abstractmethod
    def init(self) -> None:
        pass

class Grid(Env):
    """
    Class for discrete 2-d grid map.
    """
    def __init__(self, points,size,resolution) -> None:
        self.size = size
        self.resolution = resolution
        self.x_range = int((size[1] - size[0]) // resolution)  # x 方向网格数量
        self.y_range = int((size[1] - size[0]) // resolution)  # y 方向网格数量

        super().__init__(self.x_range, self.y_range)
        # allowed motions
        self.motions = [Node((-1, 0), None, 1, None), Node((-1, 1),  None, sqrt(2), None),
                        Node((0, 1),  None, 1, None), Node((1, 1),   None, sqrt(2), None),
                        Node((1, 0),  None, 1, None), Node((1, -1),  None, sqrt(2), None),
                        Node((0, -1), None, 1, None), Node((-1, -1), None, sqrt(2), None)]
        # obstacles
        self.obstacles = None
        self.obstacles_tree = None
        # Initialize obstacles and obstacle tree
        self.obstacles = None
        self.obstacles_tree = None

        # Generate obstacles from points
        self.init(points)
    
    def init(self, points) -> None:
        """
        Initialize grid map and generate obstacles from points.

        参数:
        - points: 点云数据，表示障碍物点
        """
        x_min, x_max = self.size
        y_min, y_max = self.size
        resolution = self.resolution
        obstacles = set()

        # Convert points to grid positions
        for point in points:
            grid_pos = self.get_point_grid_position(point)
            if grid_pos is not None:
                obstacles.add(grid_pos)

        # Add boundary of environment
        for i in range(self.x_range):
            obstacles.add((i, 0))
            obstacles.add((i, self.y_range - 1))
        for i in range(self.y_range):
            obstacles.add((0, i))
            obstacles.add((self.x_range - 1, i))

        self.obstacles = obstacles
        self.obstacles_tree = cKDTree(np.array(list(obstacles)))

    def update(self, obstacles):
        self.obstacles = obstacles 
        self.obstacles_tree = cKDTree(np.array(list(obstacles)))
    def get_point_grid_position(self, point):
        """
        计算某个点在网格中的位置。

        参数:
        - point: 点的坐标 (x, y)

        返回:
        - 网格坐标索引 (x_index, y_index)，如果点不在范围内返回 None
        """
        x_min, x_max = self.size
        y_min, y_max = self.size
        resolution = self.resolution

        x_index = int((point[0] - x_min) // resolution)
        y_index = int((point[1] - y_min) // resolution)

        # 检查点是否在网格范围内
        if x_min <= point[0] < x_max and y_min <= point[1] < y_max:
            return (x_index, y_index)  # 返回网格索引
        else:
            return None  # 如果点不在范围内，返回 None

    def inflate_obstacles(self, robot_radius):
        """
        膨胀障碍物，考虑机器人的体积。

        参数:
        - robot_radius: 机器人的半径（单位与网格坐标一致）
        """
        if self.obstacles is None:
            raise ValueError("Obstacles are not initialized.")

        # 计算膨胀范围的网格距离
        inflation_range = int(np.ceil(robot_radius / self.resolution))
        
        # 存储膨胀后的障碍物
        inflated_obstacles = set()

        for obs in self.obstacles:
            # 遍历每个障碍物点，并在其周围膨胀
            for dx in range(-inflation_range, inflation_range + 1):
                for dy in range(-inflation_range, inflation_range + 1):
                    # 检查是否在圆形范围内（考虑机器人是圆形）
                    if dx**2 + dy**2 <= inflation_range**2:
                        inflated_point = (obs[0] + dx, obs[1] + dy)
                        # 检查膨胀后的点是否在网格范围内
                        if 0 <= inflated_point[0] < self.x_range and 0 <= inflated_point[1] < self.y_range:
                            inflated_obstacles.add(inflated_point)

        # 更新障碍物
        self.obstacles = inflated_obstacles
        self.obstacles_tree = cKDTree(np.array(list(self.obstacles)))


class Map(Env):
    """
    Class for continuous 2-d map.
    """
    def __init__(self, x_range: int, y_range: int) -> None:
        super().__init__(x_range, y_range)
        self.boundary = None
        self.obs_circ = None
        self.obs_rect = None
        self.init()

    def init(self):
        """
        Initialize map.
        """
        x, y = self.x_range, self.y_range

        # boundary of environment
        self.boundary = [
            [0, 0, 1, y],
            [0, y, x, 1],
            [1, 0, x, 1],
            [x, 1, 1, y]
        ]

        self.obs_rect = [
            [0,0,0,0],
        ]
        self.obs_circ = [
            [0, 0, 0],
        ]

    def update(self, boundary, obs_circ, obs_rect):
        self.boundary = boundary if boundary else self.boundary
        self.obs_circ = obs_circ if obs_circ else self.obs_circ
        self.obs_rect = obs_rect if obs_rect else self.obs_rect
