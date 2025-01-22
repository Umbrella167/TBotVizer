import random

from config.DynamicConfig import RUN_TIME
from ui.boxes.NodeEditor.node_utils.BaseNode import BaseNode


class RandomInt(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "res": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
            # "pos": {"attribute_type": None, "data_type": "CONFIG", "user_data": {"value": None}},
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)
        self.automatic = True


    def func(self):
        if (self.parent.now_time - RUN_TIME) % 0.5 < 0.01:
            self.data["res"]["user_data"]["value"] = random.randint(0, 100)
