import time
import pickle
import tbkpy._core as tbkpy

if __name__ == '__main__':
    can32 = tbkpy.EPInfo()
    can32.name = "RPM"
    can32.msg_name = "MOTOR_CONTROL_31"
    can32.msg_type = "int"
    publisher31 = tbkpy.Publisher(can32)

    can32 = tbkpy.EPInfo()
    can32.name = "RPM"
    can32.msg_name = "MOTOR_CONTROL_32"
    can32.msg_type = "int"
    publisher32 = tbkpy.Publisher(can32)

    i = 0
    while True:
        i+=1
        publisher31.publish(pickle.dumps(f"{i}_data"))
        time.sleep(1)
        i+=1
        publisher32.publish(pickle.dumps(f"{i}_data"))
        time.sleep(1)
