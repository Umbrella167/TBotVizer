import time

from ui.boxes.NodeEditor.node_utils import BaseNode
from ui.components.TBKManager.ParamData import ParamData


class ParamHandler(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "prefix": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "name": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "type": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "info": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "value": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
        }
        kwargs["init_data"] = kwargs.get("init_data") or default_init_data
        super().__init__(**kwargs)
        self.param_data = None
        self.old_param_data = None
        self.automatic = True
        self.is_create = False
        self.stabilization_flag_data = None
        # 防抖相关属性
        self.last_update_time = 0
        self.DEBOUNCE_DELAY = 1

    def func(self):
        prefix = self.data["prefix"]["user_data"].get("value")
        name = self.data["name"]["user_data"].get("value")
        type = self.data["type"]["user_data"]["value"]
        info = self.data["info"]["user_data"]["value"]
        value = self.data["value"]["user_data"]["value"]

        # 如果不一样说明更新了
        if self.stabilization_flag_data != (prefix, name, type, info, value):
            self.last_update_time = time.time()
        self.stabilization_flag_data = (prefix, name, type, info, value)
        if time.time() - self.last_update_time < self.DEBOUNCE_DELAY:
            return
        self._process_param_data(prefix, name, type, info, value)

    def _process_param_data(self, prefix, name, type, info, value):
        if all([prefix, name]):
            self.param_data = ParamData(prefix=prefix, name=name)

        if self.old_param_data != (self.param_data.type, self.param_data.info, self.param_data.value):
            self.data["type"]["user_data"]["value"] = self.param_data.type
            self.data["info"]["user_data"]["value"] = self.param_data.info
            self.data["value"]["user_data"]["value"] = self.param_data.value
        elif self.old_param_data != (type, info, value):
            self.param_data.type = type
            self.param_data.info = info
            self.param_data.value = value

        self.old_param_data = (type, info, value)
