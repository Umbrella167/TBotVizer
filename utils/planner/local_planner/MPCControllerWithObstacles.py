import casadi as ca
import numpy as np
import time

import casadi as ca
import numpy as np
import time


class MPCController:
    def __init__(self, T=0.2, N=10, v_max=1, omega_max=np.pi / 3.0, a_max=0.3, rob_diam=0.3):
        self.T = T
        self.N = N
        self.v_max = v_max
        self.omega_max = omega_max
        self.a_max = a_max
        self.rob_diam = rob_diam  # Robot diameter

        # Define optimization problem
        self.opti = ca.Opti()
        self.opt_controls = self.opti.variable(N, 3)
        self.vx = self.opt_controls[:, 0]
        self.vy = self.opt_controls[:, 1]
        self.omega = self.opt_controls[:, 2]

        self.opt_states = self.opti.variable(N + 1, 3)
        self.x = self.opt_states[:, 0]
        self.y = self.opt_states[:, 1]
        self.theta = self.opt_states[:, 2]

        self.opt_x0 = self.opti.parameter(3)  # Initial state parameter
        self.opt_xs = self.opti.parameter(3)  # Target state parameter

        self.f = lambda x_, u_: ca.vertcat(
            *[
                u_[1] * ca.cos(x_[2]) - u_[0] * ca.sin(x_[2]),  # v_y * cos(theta) - v_x * sin(theta)
                u_[1] * ca.sin(x_[2]) + u_[0] * ca.cos(x_[2]),  # v_y * sin(theta) + v_x * cos(theta)
                u_[2]  # omega
            ]
        )
        self.f_np = lambda x_, u_: np.array(
            [
                u_[1] * ca.cos(x_[2]) - u_[0] * ca.sin(x_[2]),  # v_y * cos(theta) - v_x * sin(theta)
                u_[1] * ca.sin(x_[2]) + u_[0] * ca.cos(x_[2]),  # v_y * sin(theta) + v_x * cos(theta)
                u_[2]  # omega
            ]
        )
        # Initial condition constraints
        self.opti.subject_to(self.opt_states[0, :] == self.opt_x0.T)
        for i in range(N):
            x_next = self.opt_states[i, :] + self.f(self.opt_states[i, :], self.opt_controls[i, :]).T * T
            self.opti.subject_to(self.opt_states[i + 1, :] == x_next)

        # Cost function
        Q = np.diag([10.0, 10.0, 1.0])  # State weight
        R = np.diag([1.0, 1.0, 0.5])  # Control weight
        obj = 0
        for i in range(N):
            obj += ca.mtimes(
                [(self.opt_states[i, :] - self.opt_xs.T), Q, (self.opt_states[i, :] - self.opt_xs.T).T]
            ) + ca.mtimes([self.opt_controls[i, :], R, self.opt_controls[i, :].T])
        self.opti.minimize(obj)

        # Boundaries
        self.opti.subject_to(self.opti.bounded(-v_max, self.vx, v_max))
        self.opti.subject_to(self.opti.bounded(-v_max, self.vy, v_max))
        self.opti.subject_to(self.opti.bounded(-omega_max, self.omega, omega_max))
        for i in range(N - 1):
            self.opti.subject_to(
                self.opti.bounded(-a_max * T, self.opt_controls[i + 1, 0] - self.opt_controls[i, 0], a_max * T)
            )  # v_x
            self.opti.subject_to(
                self.opti.bounded(-a_max * T, self.opt_controls[i + 1, 1] - self.opt_controls[i, 1], a_max * T)
            )  # v_y
            self.opti.subject_to(
                self.opti.bounded(-a_max * T, self.opt_controls[i + 1, 2] - self.opt_controls[i, 2], a_max * T)
            )  # omega

        # Obstacle list
        self.obstacles = []

        # Solver settings
        opts_setting = {
            "ipopt.max_iter": 1000,
            "ipopt.print_level": 0,
            "print_time": 0,
            "ipopt.acceptable_tol": 1e-8,
            "ipopt.acceptable_obj_change_tol": 1e-6,
        }
        self.opti.solver("ipopt", opts_setting)

        # Initialize internal variables
        self.u0 = np.zeros((N, 3))  # Initial guess for controls
        self.next_states = np.zeros((N + 1, 3))  # Predicted states

    def add_obstacle(self, points, obs_radius):
        """
        Add a circular obstacle.
        :param obs_x: x-coordinate of the obstacle
        :param obs_y: y-coordinate of the obstacle
        :param obs_radius: radius of the obstacle
        """
        for point in points:
            print(point)

            obs_x, obs_y,_ = point
            self.obstacles.append((obs_x, obs_y, obs_radius))
        # Add constraints for the new obstacle
        for i in range(self.N + 1):  # Constraints over the horizon
            self.opti.subject_to(
                ca.sqrt((self.opt_states[i, 0] - obs_x) ** 2 + (self.opt_states[i, 1] - obs_y) ** 2)
                >= (self.rob_diam / 2 + obs_radius)
            )
    
    def shift(self, t0, x0, u, x_n):
        f_np = self.f_np
        f_value = f_np(x0, u[0])
        st = x0 + self.T * f_value
        t = t0 + self.T
        u_end = np.concatenate((u[1:], u[-1:]))
        x_n = np.concatenate((x_n[1:], x_n[-1:]))
        return t, st, u_end, x_n

    def compute_control(self, current_state, target_state):
        # Set parameters
        self.opti.set_value(self.opt_x0, current_state)
        self.opti.set_value(self.opt_xs, target_state)

        # Set initial guesses
        self.opti.set_initial(self.opt_controls, self.u0)
        self.opti.set_initial(self.opt_states, self.next_states)

        # Solve optimization problem
        sol = self.opti.solve()

        # Extract control outputs
        u_res = sol.value(self.opt_controls)
        self.u0 = u_res  # Update initial guess for controls
        self.next_states = sol.value(self.opt_states)  # Update predicted states

        # Update current state and time
        _, next_state, _, _ = self.shift(0, current_state, u_res, self.next_states)

        return u_res[0], next_state

    def generate_path_with_angles(self, start, end, path):
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

    def interpolate_path(self, points, step=0.1):
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
