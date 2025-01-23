from tzcp.ros.sensor_pb2 import IMU
from utils.Utils import convert_to_float
from ui.boxes.NodeEditor.node_utils.BaseNode import BaseNode


class ParseIMU(BaseNode):
    """
    解析序列化的 IMU 消息并提取四元数、加速度和角速度。
    """

    def __init__(self, **kwargs):
        default_init_data = {
            "serialized_imu_msg": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": None}
            },
            "imu_data": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": None}
            },
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data":
                    {"value": None}
            }
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)

    def func(self):
        serialized_imu_msg = self.data["serialized_imu_msg"]["user_data"]["value"]
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
            self.data["imu_data"]["user_data"]["value"] = gyro[2]
        else:
            # 如果没有输入数据，输出为空或保持默认值
            self.data["imu_data"]["user_data"]["value"] = None