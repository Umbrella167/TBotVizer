import numpy as np
from heapq import heappush, heappop

class AStar:
    def __init__(self, grid):
        """
        初始化 A* 算法实例。

        Parameters:
            grid (numpy.ndarray): 2D 网格，0 表示可通行，1 表示障碍。
        """
        self.grid = grid
        self.rows, self.cols = grid.shape

    def heuristic(self, a, b):
        """
        启发式函数，使用曼哈顿距离。

        Parameters:
            a, b (tuple): 两个点的坐标 (x, y)。

        Returns:
            float: 启发式估计值。
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, node):
        """
        获取节点的邻居（上下左右）。

        Parameters:
            node (tuple): 当前节点的坐标 (x, y)。

        Returns:
            list: 邻居节点的坐标列表。
        """
        x, y = node
        neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [
            (nx, ny)
            for nx, ny in neighbors
            if 0 <= nx < self.rows and 0 <= ny < self.cols
        ]

    def reconstruct_path(self, came_from, current):
        """
        重构从起点到终点的路径。

        Parameters:
            came_from (dict): 路径字典，记录每个节点的前驱节点。
            current (tuple): 当前节点的坐标。

        Returns:
            list: 从起点到终点的路径。
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def find_path(self, start, end):
        """
        使用 A* 算法查找从起点到终点的路径。

        Parameters:
            start (tuple): 起点坐标 (x, y)。
            end (tuple): 终点坐标 (x, y)。

        Returns:
            list: 从起点到终点的路径（包含每个点的 (x, y) 坐标）。
                  如果路径不存在，则返回空列表。
        """
        # 初始化开启列表 (open set) 和关闭列表 (closed set)
        open_set = []
        closed_set = np.zeros_like(self.grid, dtype=bool)

        # g_score 和 f_score
        g_score = np.full_like(self.grid, np.inf, dtype=np.float64)
        f_score = np.full_like(self.grid, np.inf, dtype=np.float64)

        # 起点设置
        start = tuple(start)
        end = tuple(end)
        g_score[start] = 0
        f_score[start] = self.heuristic(start, end)
        heappush(open_set, (f_score[start], start))

        # 存储路径
        came_from = {}

        # A* 主循环
        while open_set:
            # 获取 f_score 最小的节点
            _, current = heappop(open_set)

            # 如果到达终点，重构路径
            if current == end:
                return self.reconstruct_path(came_from, current)

            closed_set[current] = True

            # 遍历邻居节点
            for neighbor in self.get_neighbors(current):
                if closed_set[neighbor] or self.grid[neighbor] == 1:  # 跳过障碍或已处理节点
                    continue

                tentative_g_score = g_score[current] + 1  # 假设每步的代价为 1

                if tentative_g_score < g_score[neighbor]:
                    # 更新路径信息
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, end)

                    # 如果邻居不在 open_set 中，则添加
                    if not any(neighbor == item[1] for item in open_set):
                        heappush(open_set, (f_score[neighbor], neighbor))

        # 如果没有找到路径，返回空列表
        return []

def generate_grid_from_points(points, grid_size):
    """
    根据障碍物点生成 A* 算法使用的地图网格。

    Parameters:
        points (list): 障碍物点的列表，每个点为 (x, y)。
        grid_size (tuple): 网格大小 (rows, cols)。

    Returns: 
        numpy.ndarray: 生成的地图网格，0 表示可通行，1 表示障碍物。
    """
    rows, cols = grid_size
    grid = np.zeros((rows, cols), dtype=int)  # 初始化全 0 的网格

    # 将障碍物点映射到网格
    for point in points:
        x, y = int(point[0]), int(point[1])
        if 0 <= x < rows and 0 <= y < cols:  # 确保点在网格范围内
            grid[x, y] = 1  # 设置为障碍物

    return grid

# 测试代码
if __name__ == "__main__":
    # 创建一个示例网格
    grid = np.array([
        [0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0]
    ])

    start = (0, 0)  # 起点
    end = (4, 4)    # 终点

    # 创建 A* 实例
    astar = AStar(grid)

    # 运行 A* 算法
    path = astar.find_path(start, end)
    print("路径:", path)