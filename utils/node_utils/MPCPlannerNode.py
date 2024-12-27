from config.SystemConfig import RUN_TIME
from utils.node_utils.BaseNode import BaseNode
from utils.planner.local_planner.MPCController import MPCController
import numpy as np

def find_next_target(pose, path, distance):
    """
    找到路径中最接近 pose 的下一个目标点 (x, y, w)
    并且该目标点到 pose 的距离超过 distance。
    
    :param pose: 当前点 (x, y, w)
    :param path: 路径点列表 [(x1, y1, w1), (x2, y2, w2), ...]
    :param distance: 最小距离，超过该距离才认为是下一个目标点
    :return: 下一个目标点 (x, y, w)
    """
    pose = np.array(pose)  # 转换为 numpy 数组
    path = np.array(path)  # 转换为 numpy 数组

    # 遍历路径，找到第一个满足条件的点
    for point in path:
        # 计算当前路径点和 pose 的欧几里得距离
        dist = np.linalg.norm(point - pose)
        if dist > distance:  # 如果距离超过指定的阈值
            return point  # 返回该点

    # 如果没有找到满足条件的点，默认返回路径的最后一个点
    return path[-1]



class MPCPlannerNode(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "Path": {
                "attribute_type": "INPUT",
                "data_type": "NPINPUT",
                "user_data":
                    {"value": None}
            },
            "Pose":{
                "attribute_type": "INPUT",
                "data_type": "NPINPUT",
                "user_data":
                    {"value": None}
            },
            "Distance":{
                "attribute_type": "INPUT",
                "data_type": "SLIDER",
                "user_data":
                    {
                        "value": 100,
                        "setting":{
                            "min_value":0,
                            "max_value":1000
                        }
                    }
            },
            "V": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
            "W": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)
        self.automatic = False
        self.mpc = MPCController()
        self.t0 = 0
        self.u0 = np.zeros((self.mpc.N, 2))
        self.next_states = np.zeros((self.mpc.N + 1, 3))



    def func(self):
        pose = self.data["Pose"]["user_data"]["value"]
        path = self.data["Path"]["user_data"]["value"]
        try:
            if path is None or pose is None:
                return 
            if len(path) < 2:
                return
            if len(pose) != 3:
                return
        except:
            return 
        
        distance = self.data["Distance"]["user_data"]["value"]
        point = find_next_target(pose, path,distance)
        self.next_trajectories, self.next_controls = self.mpc.desired_command_and_trajectory(self.t0, pose, point)
        self.t0, now_pos, self.u0, self.next_states, u_res, x_m, solve_time = self.mpc.plan(
                    self.t0, pose, self.u0, self.next_states, self.next_trajectories, self.next_controls
                )
        if np.linalg.norm(path[-1] - pose) < distance / 2:
            self.data["V"]["user_data"]["value"] = 0
            self.data["W"]["user_data"]["value"] = 0
            return 
        else:
            self.data["V"]["user_data"]["value"] = u_res[0, 0]
            self.data["W"]["user_data"]["value"] = u_res[0, 1]

        pose = self.data["Pose"]["user_data"]["value"]
        