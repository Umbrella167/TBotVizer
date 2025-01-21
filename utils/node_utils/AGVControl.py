import pygame
pygame.init()

from utils.node_utils.BaseNode import BaseNode

class AGVControl(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "vx": {"attribute_type": "OUTPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "vy": {"attribute_type": "OUTPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "alphax": {"attribute_type": "OUTPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            # "pos": {"attribute_type": "CONFIG", "data_type": "CONFIG", "user_data": {"value": None}},
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)

        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joystick in self.joysticks:
            joystick.init()

        self.done = False
        self.automatic = True

    def func(self):
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

                self.data["vx"]["user_data"]["value"] = vx
                self.data["vy"]["user_data"]["value"] = -vy
                self.data["alphax"]["user_data"]["value"] = alphax


