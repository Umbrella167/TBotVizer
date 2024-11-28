from utils.Utils import convert_to_float
from utils.node_utils.BaseFunc import BaseFunc


class IncrementalPID(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {
            "measurement": None,
            "setpoint": None,
            "kp": None,
            "ki": None,
            "kd": None,
            "max_output": 1  # 默认最大输出值
        }
        self.output_data = {"control_output": None}
        self.previous_error = 0.0
        self.previous_previous_error = 0.0
        self.control_output = 0.0

    def calc(self):
        super().calc()
        measurement = convert_to_float(self.input_data["measurement"])
        setpoint = convert_to_float(self.input_data["setpoint"])
        kp = convert_to_float(self.input_data["kp"])
        ki = convert_to_float(self.input_data["ki"])
        kd = convert_to_float(self.input_data["kd"])
        max_output = convert_to_float(self.input_data["max_output"])
        # 计算误差
        error = setpoint - measurement
        error = 0 if abs(error) < 1.8 else error
        # 增量计算
        delta_output = (
                kp * (error - self.previous_error) +
                ki * error +
                kd * (error - 2 * self.previous_error + self.previous_previous_error)
        )
        # 更新控制输出
        self.control_output += delta_output
        if self.control_output > max_output:
            self.control_output = max_output
        elif self.control_output < -max_output:
            self.control_output = -max_output
        # 更新历史误差
        self.previous_previous_error = self.previous_error
        self.previous_error = error
        # 设置输出
        self.output_data["control_output"] = self.control_output


class PositionalPID(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {
            "measurement": None,
            "setpoint": None,
            "kp": None,
            "ki": None,
            "kd": None,
            "max_output": 1  # 默认最大输出值
        }
        self.output_data = {"control_output": None}
        self.previous_error = 0.0
        self.integral = 0.0

    def calc(self):
        super().calc()
        measurement = convert_to_float(self.input_data["measurement"])
        setpoint = convert_to_float(self.input_data["setpoint"])
        kp = convert_to_float(self.input_data["kp"])
        ki = convert_to_float(self.input_data["ki"])
        kd = convert_to_float(self.input_data["kd"])
        max_output = convert_to_float(self.input_data["max_output"])
        # 计算误差
        error = setpoint - measurement
        if abs(error) < 1:
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
        # 设置输出
        self.output_data["control_output"] = control_output
