from ui.boxes.NodeEditor.node_utils import BaseNode
from ui.components.TBKManager.ParamData import ParamData


class ParamHandler(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "prefix": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "MOTOR_CONTROL"}},
            "name": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "RPM"}},
            "type": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "list"}},
            "info": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "list"}},
            "value": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": "list"}},
        }
        kwargs["init_data"] = kwargs.get("init_data") or default_init_data
        super().__init__(**kwargs)
        # self.param_data = ParamData(prefix, name, type="Unknown", info="Custom param", default_value="None"))
        self.automatic = True
        self.is_create = False

    def func(self):
        prefix = self.data["name"]["user_data"].get("value")
        name = self.data["msg_name"]["user_data"].get("value")
        type = self.data["msg_type"]["user_data"].get("value")
        value = self.data["msg"]["user_data"].get("value")