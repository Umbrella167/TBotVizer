import numpy as np
from ctypes import *

class VESC_CAN_STATUS:
    VESC_ID_A = 20
    VESC_ID_B = 25
    VESC_CAN_PACKET_STATUS_1 = 0x09
    VESC_CAN_PACKET_STATUS_2 = 0x0E
    VESC_CAN_PACKET_STATUS_3 = 0x0F
    VESC_CAN_PACKET_STATUS_4 = 0x10
    VESC_CAN_PACKET_STATUS_5 = 0x1B


class VESC_PACK(Structure):
    _fields_ = [
        ("id", c_int),
        ("rpm", c_int),
        ("current", c_float),
        ("pid_pos_now", c_float),
        ("amp_hours", c_float),
        ("amp_hours_charged", c_float),
        ("watt_hours", c_float),
        ("watt_hours_charged", c_float),
        ("temp_fet", c_float),
        ("temp_motor", c_float),
        ("tot_current_in", c_float),
        ("duty", c_float),
        ("tachometer_value", c_float),
        ("input_voltage", c_float),
    ]


def buffer_get_int16(buffer, index):
    value = buffer[index] << 8 | buffer[index + 1]
    return value


def buffer_get_int32(buffer, index):
    value = (
        buffer[index] << 24
        | buffer[index + 1] << 16
        | buffer[index + 2] << 8
        | buffer[index + 3]
    )
    return value


def buffer_get_float16(buffer, scale, index):
    value = buffer_get_int16(buffer, index)
    return float(value) / scale


def buffer_get_float32(buffer, scale, index):
    value = buffer_get_int32(buffer, index)
    return float(value) / scale


class CAN_PY:
    def __init__(self):
        self.can_packet = VESC_PACK()

    def send_pos(self, _id: np.uint8, _pos: float):
        id = _id + 0x400
        data = [0, 0, 0, 0, 0, 0, 0, 0]
        pos_int = np.uint32(int(_pos * 1e6))
        data[0] = (pos_int >> 24) & 0xFF
        data[1] = (pos_int >> 16) & 0xFF
        data[2] = (pos_int >> 8) & 0xFF
        data[3] = pos_int & 0xFF
        print("SEND vesc id: {}, pos: {}, data: {}".format(id & 0xFF, pos_int, data))
        return id, data

    def send_rpm(self, _id: np.uint8, _rpm: float):
        id = int(_id) + 0x300
        data = [0, 0, 0, 0, 0, 0, 0, 0]
        rpm_int = np.int32(int(_rpm))
        data[0] = (rpm_int >> 24) & 0xFF
        data[1] = (rpm_int >> 16) & 0xFF
        data[2] = (rpm_int >> 8) & 0xFF
        data[3] = rpm_int & 0xFF
        return id, data

    def send_current(self, _id: np.uint8, _cur: float):
        id = _id + 0x100
        data = [0, 0, 0, 0, 0, 0, 0, 0]
        cur_int = np.uint32(int(_cur * 1000))
        data[0] = (cur_int >> 24) & 0xFF
        data[1] = (cur_int >> 16) & 0xFF
        data[2] = (cur_int >> 8) & 0xFF
        data[3] = cur_int & 0xFF
        print("SEND vesc id: {}, cur: {}, data: {}".format(id & 0xFF, cur_int, data))
        return id, data

    def send_pass_through(self, _id: np.uint8, _pos: float, _vel: float, _cur: float):
        id = _id + 0x3F00
        data = [0, 0, 0, 0, 0, 0, 0, 0]
        pos_int = np.uint16(int(_pos * 100))
        vel_int = np.uint16(int(_vel))
        cur_int = np.uint16(int(_cur * 1000))
        data[0] = (pos_int >> 8) & 0xFF
        data[1] = pos_int & 0xFF
        data[2] = (vel_int >> 8) & 0xFF
        data[3] = vel_int & 0xFF
        data[4] = (cur_int >> 8) & 0xFF
        data[5] = cur_int & 0xFF
        return id, data

    def msg_decode(self, data, id=None):
        if id is None:
            return None, None
        self.can_packet.id = id & 0xFF
        status_id = (id >> 8) & 0xFF
        if status_id == VESC_CAN_STATUS.VESC_CAN_PACKET_STATUS_1:
            self.can_packet.rpm = int(buffer_get_float32(data, 1, 0))
            self.can_packet.current = buffer_get_float16(data, 1e2, 4)
            self.can_packet.pid_pos_now = buffer_get_float16(data, 50.0, 6)
        if status_id == VESC_CAN_STATUS.VESC_CAN_PACKET_STATUS_2:
            self.can_packet.amp_hours = buffer_get_float32(data, 1e4, 0)
            self.can_packet.amp_hours_charged = buffer_get_float32(data, 1e4, 4)
        if status_id == VESC_CAN_STATUS.VESC_CAN_PACKET_STATUS_3:
            self.can_packet.watt_hours = buffer_get_float32(data, 1e4, 0)
            self.can_packet.watt_hours_charged = buffer_get_float32(data, 1e4, 4)
        if status_id == VESC_CAN_STATUS.VESC_CAN_PACKET_STATUS_4:
            self.can_packet.temp_fet = buffer_get_float16(data, 1e1, 0)
            self.can_packet.temp_motor = buffer_get_float16(data, 1e1, 2)
            self.can_packet.tot_current_in = buffer_get_float16(data, 1e1, 4)
            self.can_packet.duty = buffer_get_float16(data, 1e3, 6)
        if status_id == VESC_CAN_STATUS.VESC_CAN_PACKET_STATUS_5:
            self.can_packet.tachometer_value = buffer_get_float32(data, 1, 0)
            self.can_packet.input_voltage = buffer_get_float16(data, 1e1, 4)
        return id, self.can_packet


# 实例化 CAN_PY 类
_can_py = CAN_PY()