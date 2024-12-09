import numpy as np
import ast
import heapq
from utils.node_utils.BaseNode import BaseNode


class AStarNode(BaseNode):
    def __init__(self, **kwargs):
        # 初始化默认数据结构
        default_init_data = {
            "start": {  # 起点
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": "(0, 0)"}
            },
            "goal": {  # 终点
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": "(0, 0)"}
            },
            "map": {  # 地图
                "attribute_type": "INPUT",
                "data_type": "MULTILINEINPUT",
                "user_data": {"value": "[[0,0]]"}
            },
            "path": {  # 输出路径
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": []}
            },
            "pos": {  # 配置类属性
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data": {"value": None}
            }
        }
        kwargs["init_data"] = kwargs.get("init_data") or default_init_data
        super().__init__(**kwargs)

    def heuristic(self, start, goal):
        """启发式函数，使用曼哈顿距离"""
        return abs(start[0] - goal[0]) + abs(start[1] - goal[1])

    def neighbors(self, node, grid):
        """获取节点的邻居节点"""
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 上下左右四个方向
        neighbors = []
        for d in directions:
            neighbor = (node[0] + d[0], node[1] + d[1])
            if 0 <= neighbor[0] < grid.shape[0] and 0 <= neighbor[1] < grid.shape[1]:
                if grid[neighbor] == 0:  # 0 表示可通行
                    neighbors.append(neighbor)
        return neighbors

    def reconstruct_path(self, came_from, current):
        """重建路径"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def find_path(self, start, goal, grid):
        """寻找路径的主函数"""
        rows, cols = grid.shape

        open_list = []
        heapq.heappush(open_list, (0, start))  # (f_score, position)

        g_score = np.full((rows, cols), np.inf)
        g_score[start] = 0

        f_score = np.full((rows, cols), np.inf)
        f_score[start] = self.heuristic(start, goal)

        came_from = {}

        while open_list:
            _, current = heapq.heappop(open_list)
            if current == goal:
                return self.reconstruct_path(came_from, current)

            for neighbor in self.neighbors(current, grid):
                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    if not any(neighbor == item[1] for item in open_list):
                        heapq.heappush(open_list, (f_score[neighbor], neighbor))

        return None  # 如果没有找到路径

    def func(self):
        """执行路径计算的主函数"""
        start = self.data["start"]["user_data"]["value"]
        goal = self.data["goal"]["user_data"]["value"]
        map_data = self.data["map"]["user_data"]["value"]
        # map_data = np.array([
        #     [0, 1, 0],
        #     [0, 0, 0],
        #     [1, 0, 0]
        # ])

        try:
            start = ast.literal_eval(start)
            goal = ast.literal_eval(goal)
            map_data = np.array(ast.literal_eval(map_data))
            # 执行路径规划
            path = self.find_path(start, goal, map_data)
        except:
            path = None
        # 将结果存储到输出路径
        self.data["path"]["user_data"]["value"] = path if path else []