import pickle

from config.DynamicConfig import RUN_TIME
from ui.boxes.NodeEditor.node_utils import BaseNode
from ui.components.TBKManager import tbk_manager
from utils.Utils import convert_to_float
from utils.network.CommunicationManager import CommunicationManager


class Publisher(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "name": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "MOTOR_CONTROL"}},
            "msg_name": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "RPM"}},
            "msg_type": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "list"}},
            "frequency": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": 0.01}},
            "msg": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "pos": {"attribute_type": "CONFIG", "data_type": "CONFIG", "user_data": {"value": None}},
        }
        kwargs["init_data"] = kwargs.get("init_data") or default_init_data
        super().__init__(**kwargs)
        self.cm = CommunicationManager(tbk_manager)
        self.puber = None
        self.info = None
        self.automatic = True
        self.is_create = False

    def func(self):
        # 获取输入数据
        name = self.data["name"]["user_data"].get("value")
        msg_name = self.data["msg_name"]["user_data"].get("value")
        msg_type = self.data["msg_type"]["user_data"].get("value")
        frequency = convert_to_float(self.data["frequency"]["user_data"].get("value"))
        msg = self.data["msg"]["user_data"].get("value")

        # 设置最小频率为 0.01
        if frequency == 0:
            frequency = 0.01

        if name and msg_name and msg_type:
            # 如果三者不为空则创建 Publisher
            info = {
                "name": str(name),
                "msg_name": msg_name,
                "msg_type": msg_type,
            }
            if self.info != info:
                self.puber = self.cm.publisher(name=name, msg_name=msg_name, msg_type=msg_type)
                self.info = info
            self.is_create = True
        else:
            # 如果有一个为空则清除 Publisher
            self.puber = None
            self.is_create = False

        # 发布消息
        if (self.parent.now_time - RUN_TIME) % frequency < 0.01 and self.is_create:
            if self.puber:
                self.puber.publish(pickle.dumps(msg))
