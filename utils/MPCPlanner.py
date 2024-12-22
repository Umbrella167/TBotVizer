#!/usr/bin/env python
# coding=utf-8

import casadi as ca
import numpy as np
import time
import math


class MPCController:
    def __init__(self, T=0.5, N=8, rob_diam=0.3, v_max=11.1, omega_max=np.pi / 2):
        self.T = T
        self.N = N
        self.rob_diam = rob_diam
        self.v_max = v_max
        self.omega_max = omega_max
        self.opti = ca.Opti()
        self._initialize_model()

    def _initialize_model(self):
        # Control variables: linear velocity v and angular velocity omega
        self.opt_controls = self.opti.variable(self.N, 2)
        v = self.opt_controls[:, 0]
        omega = self.opt_controls[:, 1]

        # State variables
        self.opt_states = self.opti.variable(self.N + 1, 3)
        x = self.opt_states[:, 0]
        y = self.opt_states[:, 1]
        theta = self.opt_states[:, 2]

        # Parameters: reference trajectories of the pose and inputs
        self.opt_u_ref = self.opti.parameter(self.N, 2)
        self.opt_x_ref = self.opti.parameter(self.N + 1, 3)

        # Dynamics model
        self.f = lambda x_, u_: ca.vertcat(*[u_[0] * ca.cos(x_[2]), u_[0] * ca.sin(x_[2]), u_[1]])
        self.f_np = lambda x_, u_: np.array([u_[0] * np.cos(x_[2]), u_[0] * np.sin(x_[2]), u_[1]])

        # Initial condition constraint
        self.opti.subject_to(self.opt_states[0, :] == self.opt_x_ref[0, :])
        for i in range(self.N):
            x_next = self.opt_states[i, :] + self.f(self.opt_states[i, :], self.opt_controls[i, :]).T * self.T
            self.opti.subject_to(self.opt_states[i + 1, :] == x_next)

        # Define the cost function
        Q = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.5]])
        R = np.array([[0.5, 0.0], [0.0, 0.05]])
        obj = 0
        for i in range(self.N):
            state_error_ = self.opt_states[i, :] - self.opt_x_ref[i + 1, :]
            control_error_ = self.opt_controls[i, :] - self.opt_u_ref[i, :]
            obj += ca.mtimes([state_error_, Q, state_error_.T]) + ca.mtimes([control_error_, R, control_error_.T])
        self.opti.minimize(obj)

        # Boundary and control constraints
        # self.opti.subject_to(self.opti.bounded(-20.0, x, 20.0))
        # self.opti.subject_to(self.opti.bounded(-2.0, y, 2.0))
        # self.opti.subject_to(self.opti.bounded(-np.pi, theta, np.pi))
        self.opti.subject_to(self.opti.bounded(-self.v_max, v, self.v_max))
        self.opti.subject_to(self.opti.bounded(-self.omega_max, omega, self.omega_max))

        # Solver settings
        opts_setting = {
            "ipopt.max_iter": 2000,
            "ipopt.print_level": 0,
            "print_time": 0,
            "ipopt.acceptable_tol": 1e-8,
            "ipopt.acceptable_obj_change_tol": 1e-6,
        }
        self.opti.solver("ipopt", opts_setting)

    def shift_movement(self, t0, x0, u, x_n):
        f_value = self.f_np(x0, u[0])
        st = x0 + self.T * f_value
        t = t0 + self.T
        u_end = np.concatenate((u[1:], u[-1:]))
        x_n = np.concatenate((x_n[1:], x_n[-1:]))
        return t, st, u_end, x_n

    def desired_command_and_trajectory(self, t, x0_,target):
        x_ = np.zeros((self.N + 1, 3))
        x_[0] = x0_
        u_ = np.zeros((self.N, 2))
        x,y,theta = target
        for i in range(self.N):
            x_ref_ = x
            y_ref_ = y
            theta_ref_ = theta
            

            v_ref_ = 0.5
            omega_ref_ = 0.0
            # if x_ref_ >= 12.0:
            #     x_ref_ = 12.0
            #     v_ref_ = 0.0
            x_[i + 1] = np.array([x_ref_, y_ref_, theta_ref_])
            u_[i] = np.array([v_ref_, omega_ref_])
        return x_, u_

    def plan(self, t0, current_state, u0, next_states, next_trajectories, next_controls):
        """
        Perform one step of the MPC planning process.
        """
        # Set parameters
        self.opti.set_value(self.opt_x_ref, next_trajectories)
        self.opti.set_value(self.opt_u_ref, next_controls)
        self.opti.set_initial(self.opt_controls, u0.reshape(self.N, 2))
        self.opti.set_initial(self.opt_states, next_states)

        # Solve the problem
        t_ = time.time()
        sol = self.opti.solve()
        solve_time = time.time() - t_

        # Obtain results
        u_res = sol.value(self.opt_controls)
        x_m = sol.value(self.opt_states)

        # Update the state
        t0, current_state, u0, next_states = self.shift_movement(t0, current_state, u_res, x_m)

        return t0, current_state, u0, next_states, u_res, x_m, solve_time

    def run(self, init_state,target,sim_time=60.0):
        t0 = 0
        current_state = init_state.copy()
        u0 = np.zeros((self.N, 2))
        next_trajectories = np.tile(init_state, self.N + 1).reshape(self.N + 1, -1)
        next_controls = np.zeros((self.N, 2))
        next_states = np.zeros((self.N + 1, 3))
        x_c = []
        u_c = []
        t_c = [t0]
        xx = []
        mpciter = 0
        start_time = time.time()
        index_t = []

        # while mpciter - sim_time / self.T < 0.0:
        # while mpciter - sim_time / self.T < 0.0:
        while np.linalg.norm(current_state[:2] - target[:2]) > 1:
            if mpciter > 2000:
                break 
            # Call the plan function for one step of MPC
            t0, current_state, u0, next_states, u_res, x_m, solve_time = self.plan(
                t0, current_state, u0, next_states, next_trajectories, next_controls
            )

            # Collect results
            index_t.append(solve_time)
            u_c.append(u_res[0, :])
            t_c.append(t0)
            x_c.append(x_m)
            xx.append(current_state)

            # Update desired trajectories and controls
            next_trajectories, next_controls = self.desired_command_and_trajectory(t0, current_state,target)
            mpciter += 1
        return xx, u_c
    
    def generate_path_with_angles(self,start,end,path):
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
            x1, y1 = path[i-1]
            # 下一个点
            x2, y2 = path[i]
            # 计算方向角 (atan2)
            direction = np.arctan2(y2 - y1, x2 - x1)
            path_with_angles.append((x2, y2, direction))
        
        path_with_angles.append(end)
        return path_with_angles

# Example of usage
if __name__ == "__main__":
    # mpc = MPCController()
    # mpc.run()
    path = [
        [1,1],
        [2,2],
        [3,3],
        [4,4],
        [5,5],
        [6,6],
        [7,7],
        [8,8],
        [9,9],
        [10,10],
        [11,11],
        [12,12],
        [13,13],
        [14,14],
        [15,15],
        [16,16],
        [17,17],
        [18,18],
        [19,19],
        [20,20]
    ]
    mpc = MPCController()

    now_state = np.array([0.0, 0.0, 0.0])
    end = np.array([20.0, 20.0, math.pi / 2])
    path = mpc.generate_path_with_angles(now_state, end, path)

    t0 = 0
    u0 = np.zeros((mpc.N, 2))
    next_states = np.zeros((mpc.N + 1, 3))
    next_trajectories, next_controls = mpc.desired_command_and_trajectory(t0, now_state, path[0])

    while np.linalg.norm(now_state[:2] - end[:2]) > 0.5:
        for point in path:
            while np.linalg.norm(now_state[:2] - np.array(point[:2])) > 0.5:
                # 调用 MPC 进行一步规划
                t0, now_state, u0, next_states, u_res, x_m, solve_time = mpc.plan(
                    t0, now_state, u0, next_states, next_trajectories, next_controls
                )
                next_trajectories, next_controls = mpc.desired_command_and_trajectory(t0, now_state, point)
                # 打印调试信息
                print(f"Current state: {now_state}, Target point: {point}")