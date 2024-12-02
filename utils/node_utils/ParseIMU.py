from tzcp.ros.sensor_pb2 import IMU

from utils.Utils import convert_to_float
from utils.node_utils.BaseNode import BaseNode
import pylinalg as la

class ParseIMU(BaseNode):
    """
    解析序列化的 IMU 消息并提取四元数、加速度和角速度。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {"serialized_imu_msg": None}  # 输入：序列化的 IMU 消息
        self.output_data = {"imu_data": None}  # 输出：解析后的 IMU 数据字典

    def calc(self):
        super().calc()
        serialized_imu_msg = self.input_data.get("serialized_imu_msg")
        if serialized_imu_msg is not None:
            imu_msg = IMU()
            imu_msg.ParseFromString(serialized_imu_msg)

            # 解析四元数 (Quaternion)
            quat = [
                convert_to_float(imu_msg.orientation.x),
                convert_to_float(imu_msg.orientation.y),
                convert_to_float(imu_msg.orientation.z),
                convert_to_float(imu_msg.orientation.w),
            ]

            # 解析线性加速度 (Linear Acceleration)
            acc = [
                convert_to_float(imu_msg.linear_acceleration.x),
                convert_to_float(imu_msg.linear_acceleration.y),
                convert_to_float(imu_msg.linear_acceleration.z),
            ]

            # 解析角速度 (Angular Velocity)
            gyro = [
                convert_to_float(imu_msg.angular_velocity.x),
                convert_to_float(imu_msg.angular_velocity.y),
                convert_to_float(imu_msg.angular_velocity.z),
            ]

            # 构建输出字典
            self.output_data["imu_data"] = gyro[2]

        else:
            # 如果没有输入数据，输出为空或保持默认值
            self.output_data["imu_data"] = None
