#!/usr/bin/env python
# coding=utf-8

import casadi as ca
import numpy as np
import time



class MPCPlanner:
    def __init__(self, T=0.5, N=8, rob_diam=0.3, v_max=4.6, omega_max=np.pi):
        self.T = T  # Time step
        self.N = N  # Prediction horizon
        self.rob_diam = rob_diam
        self.v_max = v_max
        self.omega_max = omega_max

        # Initialize optimizer
        self.opti = ca.Opti()
        self.opt_controls = self.opti.variable(N, 2)
        self.v = self.opt_controls[:, 0]
        self.omega = self.opt_controls[:, 1]
        self.opt_states = self.opti.variable(N+1, 3)
        self.x = self.opt_states[:, 0]
        self.y = self.opt_states[:, 1]
        self.theta = self.opt_states[:, 2]

        # Reference trajectories
        self.opt_u_ref = self.opti.parameter(N, 2)
        self.opt_x_ref = self.opti.parameter(N+1, 3)

        # Model dynamics
        self.f = lambda x_, u_: ca.vertcat(*[u_[0]*ca.cos(x_[2]), u_[0]*ca.sin(x_[2]), u_[1]])
        self.f_np = lambda x_, u_: np.array([u_[0]*np.cos(x_[2]), u_[0]*np.sin(x_[2]), u_[1]])

        # Initial conditions
        self.opti.subject_to(self.opt_states[0, :] == self.opt_x_ref[0, :])
        for i in range(N):
            x_next = self.opt_states[i, :] + self.f(self.opt_states[i, :], self.opt_controls[i, :]).T * T
            self.opti.subject_to(self.opt_states[i+1, :] == x_next)

        # Cost function
        Q = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.5]])
        R = np.array([[0.5, 0.0], [0.0, 0.05]])
        obj = 0
        for i in range(N):
            state_error_ = self.opt_states[i, :] - self.opt_x_ref[i+1, :]
            control_error_ = self.opt_controls[i, :] - self.opt_u_ref[i, :]
            obj += ca.mtimes([state_error_, Q, state_error_.T]) + ca.mtimes([control_error_, R, control_error_.T])
        self.opti.minimize(obj)

        # Constraints
        # self.opti.subject_to(self.opti.bounded(-20.0, self.x, 20.0))
        # self.opti.subject_to(self.opti.bounded(-2.0, self.y, 2.0))
        self.opti.subject_to(self.opti.bounded(-np.pi, self.theta, np.pi))
        self.opti.subject_to(self.opti.bounded(-self.v_max, self.v, self.v_max))
        self.opti.subject_to(self.opti.bounded(-self.omega_max, self.omega, self.omega_max))

        # Solver settings
        opts_setting = {'ipopt.max_iter': 2000, 'ipopt.print_level': 0, 'print_time': 0,
                        'ipopt.acceptable_tol': 1e-8, 'ipopt.acceptable_obj_change_tol': 1e-6}
        self.opti.solver('ipopt', opts_setting)

    def shift_movement(self, T, t0, x0, u, x_n, f):
        f_value = f(x0, u[0])
        st = x0 + T * f_value
        t = t0 + T
        u_end = np.concatenate((u[1:], u[-1:]))
        x_n = np.concatenate((x_n[1:], x_n[-1:]))
        return t, st, u_end, x_n

    def desired_command_and_trajectory(self, waypoints, T, x0_, N_):
        # Generate reference trajectory from waypoints
        x_ = np.zeros((N_+1, 3))
        x_[0] = x0_
        u_ = np.zeros((N_, 2))
        for i in range(N_):
            waypoint_idx = min(i, len(waypoints) - 1)
            x_ref_, y_ref_ = waypoints[waypoint_idx]
            theta_ref_ = 0.0
            v_ref_ = 0.5
            omega_ref_ = 0.0
            x_[i+1] = np.array([x_ref_, y_ref_, theta_ref_])
            u_[i] = np.array([v_ref_, omega_ref_])
        return x_, u_

    def plan(self, start, end, path=None):
        if path is None:
            path = []
        waypoints = [start[:2]] + path + [end[:2]]

        t0 = 0
        init_state = np.array(start)
        current_state = init_state.copy()
        u0 = np.zeros((self.N, 2))
        next_trajectories = np.tile(init_state, self.N+1).reshape(self.N+1, -1)
        next_controls = np.zeros((self.N, 2))
        next_states = np.zeros((self.N+1, 3))
        x_c = []
        u_c = []
        t_c = [t0]
        xx = []
        sim_time = 30.0

        # Start MPC
        mpciter = 0
        while mpciter - sim_time / self.T < 0.0:
            self.opti.set_value(self.opt_x_ref, next_trajectories)
            self.opti.set_value(self.opt_u_ref, next_controls)
            self.opti.set_initial(self.opt_controls, u0.reshape(self.N, 2))
            self.opti.set_initial(self.opt_states, next_states)
            sol = self.opti.solve()
            u_res = sol.value(self.opt_controls)
            x_m = sol.value(self.opt_states)
            u_c.append(u_res[0, :])
            t_c.append(t0)
            x_c.append(x_m)
            t0, current_state, u0, next_states = self.shift_movement(self.T, t0, current_state, u_res, x_m, self.f_np)
            xx.append(current_state)
            next_trajectories, next_controls = self.desired_command_and_trajectory(waypoints, self.T, current_state, self.N)
            mpciter += 1

        # Draw the result
        return xx

# Usage example:
if __name__ == '__main__':
    planner = MPCPlanner()
    start = (10, 10, 0)  # Initial state (x, y, theta)
    end = (126, 76, 0)  # Final state (x, y, theta)[10, 10, 0] [126, 76, 0]
    path = [(15.408116424030021, 12.022345401680695), (17.051750109773142, 13.161848937037426), (18.232543040005815, 14.776075704227383), (19.693758476004774, 16.14167061107142), (21.43648160512437, 17.12295349344102), (23.42510706454867, 17.33595298200731), (25.050984935124582, 18.50065086127538), (26.17323880564245, 20.156110389656448), (27.634274711804267, 21.52189737191463), (28.33368000939684, 23.39561886394578), (28.323778788395405, 25.395594355251284), (30.099603679144295, 26.315619331758278), (30.052232456737006, 28.315058244875566), (31.86980282867042, 29.14958682022205), (33.6602876713887, 30.0407456321047), (34.292682825613355, 31.938132353074668), (36.14554165402199, 32.69106937699378), (38.11117590679057, 33.060233276018174), (38.797608684588276, 34.938745996647164), (40.36960511441172, 36.17520352710357), (41.966980968054756, 37.378694441983356), (43.16409971912804, 38.98085133062715), (45.161478543808265, 39.08321260611269), (47.05039757670952, 39.74046817827878), (48.31271957161667, 41.291771881998216), (50.102895625101816, 42.183550833044016), (51.61171872529042, 43.49635426552629), (52.75368461150983, 45.13827811111448), (53.153503543218825, 47.09790685703731), (53.88604923000712, 48.95892185342177), (55.88345095738326, 48.85700846139309), (57.748577288985686, 49.579022150434575), (59.145514027789474, 51.010304005199814), (59.93946972298125, 49.737689323338586), (60.998097601388366, 48.04083723342054), (62.05672547979549, 46.34398514350249), (63.11535335820261, 44.64713305358445), (64.17398123660973, 42.9502809636664), (65.23260911501686, 41.253428873748355), (66.96882028315923, 42.24618804878411), (68.70503145130161, 43.23894722381988), (70.44124261944398, 44.231706398855636), (72.17745378758636, 45.22446557389139), (73.91366495572873, 46.21722474892716), (75.64987612387111, 47.209983923962916), (77.38608729201349, 48.20274309899868), (79.12229846015586, 49.19550227403444), (80.85850962829824, 50.188261449070204), (82.59472079644061, 51.18102062410596), (84.33093196458299, 52.17377979914173), (86.06714313272536, 53.16653897417749), (87.80335430086774, 54.15929814921326), (89.53956546901011, 55.15205732424902), (91.27577663715249, 56.14481649928479), (93.01198780529486, 57.13757567432055), (94.74819897343724, 58.130334849356316), (96.48441014157962, 59.12309402439208), (98.22062130972199, 60.115853199427846), (99.95683247786437, 61.10861237446361), (101.69304364600674, 62.101371549499376), (103.42925481414912, 63.09413072453514), (105.1654659822915, 64.0868898995709), (106.90167715043387, 65.07964907460666), (108.63788831857624, 66.07240824964242), (110.37409948671862, 67.06516742467818), (112.110310654861, 68.05792659971394), (113.84652182300337, 69.0506857747497), (115.58273299114575, 70.04344494978545), (117.31894415928812, 71.03620412482121), (119.0551553274305, 72.02896329985697), (120.79136649557287, 73.02172247489273), (122.52757766371525, 74.01448164992848), (124.26378883185762, 75.00724082496424)]
    result = planner.plan(start, end, path)
    print("Planned trajectory:", result)

