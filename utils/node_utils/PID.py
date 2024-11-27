import time

from utils.node_utils.BaseFunc import BaseFunc


class PID(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 输入数据
        self.input_data = {
            "setpoint": None,  # 目标值
            "process_variable": None,  # 当前值
            "kp": None,  # 比例增益
            "ki": None,  # 积分增益
            "kd": None,  # 微分增益
        }
        # 输出数据
        self.output_data = {"control_output": None}
        # 内部变量
        self._prev_error = 0  # 前一次误差
        self._integral = 0  # 积分项
        self._prev_time = None  # 前一次计算时间

    def calc(self):
        super().calc()
        # 获取当前时间
        current_time = time.time()
        dt = 0
        if self._prev_time is not None:
            dt = current_time - self._prev_time
        self._prev_time = current_time
        # 获取输入数据
        setpoint = self._convert_to_float(self.input_data["setpoint"])
        process_variable = self._convert_to_float(self.input_data["process_variable"])
        kp = self._convert_to_float(self.input_data["kp"])
        ki = self._convert_to_float(self.input_data["ki"])
        kd = self._convert_to_float(self.input_data["kd"])
        # 计算误差
        error = setpoint - process_variable
        # 计算积分项
        if dt > 0:
            self._integral += error * dt
        # 计算微分项
        derivative = 0
        if dt > 0:
            derivative = (error - self._prev_error) / dt
        # 计算控制输出
        control_output = kp * error + ki * self._integral + kd * derivative
        # 更新输出
        self.output_data["control_output"] = control_output
        # 存储当前误差作为下一次的前一次误差
        self._prev_error = error

    def _convert_to_float(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0
