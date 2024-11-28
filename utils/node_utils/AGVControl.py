from time import sleep

import pygame
import time
from utils.node_utils.BaseFunc import BaseFunc

class AGVControl(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_data = {"vx": None, "vy": None, "alphax":None}

        pygame.init()
        pygame.joystick.init()
        # 初始化所有操纵杆
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joystick in self.joysticks:
            joystick.init()

        self.done = False


    def calc(self):
        if not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True

            for joystick in self.joysticks:
                vx = joystick.get_axis(0)  # X轴
                vy = joystick.get_axis(1)  # Y轴
                alphax = joystick.get_axis(3)  # 旋转轴

                buttons = [joystick.get_button(i) for i in range(4)]
                vy = (-1 * buttons[3]) + (1 * buttons[0]) or vy
                vx = (1 * buttons[1]) + (-1 * buttons[2]) or vx

                # 死区处理
                vx = vx * (abs(vx) >= 0.1)
                vy = vy * (abs(vy) >= 0.1)
                alphax = alphax * (abs(alphax) >= 0.1)

                # 更新输出数据
                self.output_data["vx"] = vx
                self.output_data["vy"] = vy
                self.output_data["alphax"] = alphax
                # 数据检查
                super().calc()
                # print(f"vx: {vx}, vy: {vy}")  # 输出结果


