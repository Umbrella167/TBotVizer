import numpy as np
from api.TBKManager import tbk_manager
import pylinalg as la
import cv2
from ui.boxes.AGV.agv_param import AGVParam
class AGVBoxUtils:
    @staticmethod
    def get_pose(odometry):
        pos = AGVBoxUtils.get_odometry_position(odometry)
        dir = AGVBoxUtils.get_odometry_rotation(odometry)
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
        path :保存的已经移动路径

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
        return cv2.flip(img, 0)


    @staticmethod
    def is_path_reachable(grid, path):
        """
        检测路径是否可达，检查路径中是否有障碍物

        参数:
        - grid: Grid 对象，有 obstacles 信息
        - path: 包含起点、拐点和终点坐标的列表

        返回:
        - bool: 如果路径可达则返回 True，否则返回 False
        """
        # 如果没有障碍物信息，默认路径可达
        if not grid.obstacles:
            return True

        # 将障碍物转换为集合以加速查找
        obstacles = set(grid.obstacles)

        # 生成路径中所有经过的格子点
        full_path_points = []
        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]
            full_path_points.extend(AGVBoxUtils.generate_line_points(start, end))

        # 检查所有路径点是否有障碍物
        return all(point not in obstacles for point in full_path_points)

    @staticmethod
    def generate_line_points(start, end):

        """
        根据两个点生成直线上的所有格子点（包括起点和终点）

        参数:
        - start: 起点坐标 (x1, y1)
        - end: 终点坐标 (x2, y2)

        返回:
        - 直线经过的所有格子点的列表
        """
        x1, y1 = start
        x2, y2 = end

        points = []

        # 使用 Bresenham 算法生成直线上的所有格子点
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

        return points
        
    @staticmethod
    def detect_collision(points, path, resolution=10,step=10):
            
        """
        检测路径是否与点集发生碰撞
        :param points: 点集 [(x1, y1), (x2, y2), ...]
        :param path: 路径 [(x1, y1), (x2, y2), ...]
        :param resolution: 网格分辨率
        :return: True 如果有碰撞，否则 False
        """

        if path is None or points is None or len(path) == 0 or len(points) == 0:
            return
        
        # 创建网格地图和归一化范围
        grid_map, (x_max, x_min, y_min, y_max) = AGVBoxUtils.create_grid_map(points, resolution)
        path = AGVBoxUtils.interpolate_path(path,step=step)

        
        # 遍历路径点，将路径映射到网格并检查碰撞
        for x, y in path:
            try:
                # 归一化路径点
                normalized_x = (x - x_min) / (x_max - x_min)
                normalized_y = (y - y_min) / (y_max - y_min)
                
                # 检查归一化后的路径点是否超出范围
                if not (0 <= normalized_x <= 1 and 0 <= normalized_y <= 1):
                    continue
                
                # 将归一化路径点映射到网格索引
                grid_x = int(normalized_x * (resolution - 1))
                grid_y = int(normalized_y * (resolution - 1))
                
                # 检查网格中是否存在物体
                if grid_map[grid_x, grid_y] == 1:
                    return True  # 碰撞发生
            except Exception as e:
                print(f"Error processing path point ({x}, {y}): {e}")
                continue

        return False  # 无碰撞

    @staticmethod
    def create_grid_map(points, resolution=10):
        """
        根据点创建网格地图。
        
        参数:
            points (list of tuple): 输入的点列表，每个点是 (x, y) 坐标。
            resolution (int): 网格的分辨率，即网格的大小或细粒度。
            
        返回:
            grid_map (numpy.ndarray): 生成的网格地图，归一化后的点映射到网格中。
        """

        
        # 提取所有点的 x 和 y 坐标
        x_coords = [point[0] for point in points]
        y_coords = [point[1] for point in points]
        
        # 找到点的最小值和最大值，用于归一化
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # 归一化点，将点的坐标映射到 [0, 1] 区间
        normalized_points = [
            ((x - x_min) / (x_max - x_min), (y - y_min) / (y_max - y_min))
            for x, y,z in points
        ]
        
        # 根据分辨率计算网格大小
        grid_size_x = resolution
        grid_size_y = resolution
        
        # 初始化网格地图，初始值为 0
        grid_map = np.zeros((grid_size_x, grid_size_y), dtype=int)
        
        for x, y in normalized_points:
            # 将归一化后的点映射到网格索引
            grid_x = int(x * (grid_size_x - 1))
            grid_y = int(y * (grid_size_y - 1))
            
            # 在网格中标记点
            grid_map[grid_x, grid_y] = 1
        
        return grid_map,(x_max,x_min,y_min,y_max)


    @staticmethod
    def generate_path_with_angles(start, end, path):
        """
        根据路径计算每个点的方向角度（弧度）。
        :param path: 路径列表，例如 [[x1, y1], [x2, y2], ...]
        :param start_dir: 起始方向角，以弧度表示，默认为 0
        :return: 带方向角的路径 [(x, y, dir), ...]
        """
        if len(path) < 2:
            raise ValueError("Path must contain at least two points to calculate directions.")

        path_with_angles = [start]

        for i in range(1, len(path)):
            # 当前点
            x1, y1 = path[i - 1]
            # 下一个点
            x2, y2 = path[i]
            # 计算方向角 (atan2)
            direction = np.arctan2(y2 - y1, x2 - x1)
            path_with_angles.append((x2, y2, direction))

        path_with_angles.append(end)
        return path_with_angles

    @staticmethod
    def interpolate_path(points, step=0.1):
        """
        使用 numpy 对路径的点进行插值以提高效率。

        参数:
        points: List[Tuple[float, float]]
            路径点的列表，每个点是一个 (x, y) 元组。
        step: float
            插值步长，默认值为 0.1。

        返回:
        List[Tuple[float, float]]
            插值后的点列表。
        """
        points = np.array(points)  # 转换为 NumPy 数组
        if len(points) < 2:
            raise ValueError("点的数量必须至少为2个才能进行插值")

        # 初始化插值的点列表
        interpolated_points = []

        # 遍历每一对相邻点
        for i in range(len(points) - 1):
            # 起点和终点
            p1, p2 = points[i], points[i + 1]

            # 计算两点之间的欧几里得距离
            distance = np.linalg.norm(p2 - p1)

            # 计算插值点的数量
            num_steps = int(distance // step)

            # 生成 t 的值 (从 0 到 1，分成 num_steps + 1 段)
            t = np.linspace(0, 1, num_steps + 1)

            # 使用线性插值公式生成插值的点
            interpolated_segment = (1 - t)[:, None] * p1 + t[:, None] * p2
            interpolated_points.append(interpolated_segment)

        # 将每段插值的结果合并为一个数组
        interpolated_points = np.vstack(interpolated_points)

        # 确保包含最后一个点
        if not np.array_equal(interpolated_points[-1], points[-1]):
            interpolated_points = np.vstack([interpolated_points, points[-1]])

        return interpolated_points.tolist()
