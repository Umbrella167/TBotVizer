from ui.boxes.BaseBox import BaseBox
import dearpygui.dearpygui as dpg
from ui.components.Canvas3D import Canvas3D
import pygfx as gfx
import pylinalg as la
from math import pi
from utils.DataProcessor import MsgSubscriberManager
from utils.ClientLogManager import client_logger
from tzcp.ros.sensor_pb2 import IMU
from utils.DataProcessor import tbk_data

class IMUBoxCallback:
    def __init__(self):
        self.msg_subscriber_manager = MsgSubscriberManager()
        pass

    def subscriber_msg(self,msg,update_angle):
        imu_data = self.parse_from_IMU(msg)

        update_angle(imu_data['quat'])

    def parse_from_IMU(self,serialized_imu_msg):
        """
        将序列化的 IMU 消息反序列化为原始字典形式。

        Args:
            serialized_imu_msg (bytes): 序列化的 IMU 消息（由 SerializeToString() 生成）。

        Returns:
            dict: 包含原始 IMU 数据的字典：
                - quat: 四元数 [x, y, z, w]
                - acc: 加速度 [x, y, z]
                - gyro: 角速度 [x, y, z]
        """
        imu_msg = IMU()
        imu_msg.ParseFromString(serialized_imu_msg)

        # 解析四元数 (Quaternion)
        quat = [
            imu_msg.orientation.x,
            imu_msg.orientation.y,
            imu_msg.orientation.z,
            imu_msg.orientation.w,
        ]

        # 解析线性加速度 (Linear Acceleration)
        acc = [
            imu_msg.linear_acceleration.x,
            imu_msg.linear_acceleration.y,
            imu_msg.linear_acceleration.z,
        ]

        # 解析角速度 (Angular Velocity)
        gyro = [
            imu_msg.angular_velocity.x,
            imu_msg.angular_velocity.y,
            imu_msg.angular_velocity.z,
        ]

        # 构建原始字典
        imu_data = {
            "quat": quat,
            "acc": acc,
            "gyro": gyro,
        }

        return imu_data

class IMUBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas3D = None
        self.count = 0
        self._callback = IMUBoxCallback()
        self.checkbox_bind = {}
    def create(self):
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="IMU3DBox")
            self.canvas3D = Canvas3D(self.tag)
            dpg.set_item_drop_callback(self.canvas3D.canvas.group_tag, callback=self.drop_callback)

        scene = self.imu_scene()
        self.canvas3D.add(scene)

    def imu_scene(self):

        self.grid = gfx.GridHelper(5000, 50, color1="#444444", color2="#222222")
        self.imu_group = gfx.Group()
        self.car_meshes = gfx.load_mesh("static/model/car.STL")[0]
        rot = la.quat_from_euler([-pi / 2, 0, -pi],order='XYZ')
        self.car_meshes.local.rotation = rot
        self.car_meshes.local.position = (0, -120, 0)

        self.AxesHelper = gfx.AxesHelper(1500, 5)

        self.AxesHelper = gfx.AxesHelper(1500, 5)
        self.AxesHelper.local.position = (-150, 0, 0)
        self.car_meshes.local.scale_x = 20
        self.car_meshes.local.scale_y = 20
        self.car_meshes.local.scale_z = 20
        self.imu_group.add(self.car_meshes, self.AxesHelper)
        return self.imu_group

    def checkbox_is_checked(self):
        for tag in self.checkbox_bind:
            puuid, msg_name, name = self.checkbox_bind[tag]
            if not dpg.get_value(tag):
                self._callback.msg_subscriber_manager.remove_subscriber(puuid, msg_name, name,self.tag)

    def drop_callback(self, sender, app_data):
        msg_info, msg_checkbox_tag = app_data
        sub_checkbox = msg_checkbox_tag["sub_checkbox"]
        msg_type = msg_info["msg_type"]
        if not dpg.get_value(sub_checkbox):
            client_logger.log("warning", f"Please subscribe to this msg")
            return
        if not msg_type == 'IMU':
            client_logger.log("ERROR", f"Unknown msg_type: {msg_type}")
            return

        name = msg_info["name"]
        msg_name = msg_info["msg_name"]
        puuid = msg_info["puuid"]
        self.checkbox_bind[sub_checkbox] = (puuid, msg_name, name)
        msg_info['tag'] = self.tag
        sub = tbk_data.Subscriber(msg_info,lambda msg: self._callback.subscriber_msg(msg,self.update_angel))

        self._callback.msg_subscriber_manager.add_subscriber(puuid,msg_name,name,self.tag,sub)

    def destroy(self):
        self._callback.msg_subscriber_manager.clear()
        super().destroy()

    def update_angel(self, rot):
        self.imu_group.local.rotation = rot

    def update(self):
        self.canvas3D.update()
