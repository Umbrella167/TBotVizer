from utils.Utils import convert_to_float
from utils.node_utils.BaseNode import BaseNode

class PositionalPID(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "measurement": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            "setpoint": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            "kp": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            "ki": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            "kd": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            # "max_output": {
            #     "attribute_type": "INPUT",
            #     "data_type": "STRINPUT",
            #     "user_data": {"value": 1}
            # },
            "control_output": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data": {"value": None}
            }
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)
        self.previous_error = 0.0
        self.integral = 0.0
        self.automatic = True

    def func(self):
        # 获取输入值
        measurement = convert_to_float(self.data["measurement"]["user_data"]["value"])
        setpoint = convert_to_float(self.data["setpoint"]["user_data"]["value"])
        kp = convert_to_float(self.data["kp"]["user_data"]["value"])
        ki = convert_to_float(self.data["ki"]["user_data"]["value"])
        kd = convert_to_float(self.data["kd"]["user_data"]["value"])
        # max_output = convert_to_float(self.data["max_output"]["user_data"]["value"])
        max_output = 1e9

        # 计算误差
        error = setpoint - measurement
        if abs(error) < 1:  # 死区范围
            error = 0

        # 积分清零逻辑：当误差符号变化时
        if (error > 0 and self.previous_error < 0) or (error < 0 and self.previous_error > 0):
            self.integral = self.integral / 2

        # 积分累加
        self.integral += error

        # 微分计算
        derivative = error - self.previous_error

        # PID计算
        control_output = (
            kp * error +
            ki * self.integral +
            kd * derivative
        )

        # 限制控制输出
        if control_output > max_output:
            control_output = max_output
        elif control_output < -max_output:
            control_output = -max_output

        # 更新历史误差
        self.previous_error = error

        # 设置输出值
        self.data["control_output"]["user_data"]["value"] = control_output