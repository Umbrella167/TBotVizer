import numpy as np
from api.NewTBKApi import tbk_manager
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
        检测路径是否可达，检查路径是否有障碍物或是否超出网格范围。

        参数:
        - grid: Grid 对象，包含 x_range, y_range 和 obstacles 信息
        - path: 路径信息，为一系列 (x, y) 坐标点的列表，表示机器人移动的路径

        返回:
        - bool: 如果路径可达则返回 True，否则返回 False
        """
        # 获取网格范围
        x_range, y_range = grid.x_range, grid.y_range

        # 检查路径中的每个点
        for x, y in path:
            # 检查是否超出网格范围
            if x < 0 or x >= x_range or y < 0 or y >= y_range:
                return False

            # 检查是否存在障碍物
            if grid.obstacles is not None and (x, y) in grid.obstacles:
                return False

        # 如果所有点都在网格范围内且没有障碍物，则路径可达
        return True