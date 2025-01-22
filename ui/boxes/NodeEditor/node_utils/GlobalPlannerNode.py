from ui.boxes.NodeEditor.node_utils.BaseNode import BaseNode
import utils.planner.python_motion_planning as pmp

class GlobalPlannerNode(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "Start": {
                "attribute_type": "INPUT",
                "data_type": "NPINPUT",
                "user_data":
                    {"value": None}
            },
            "Target":{
                "attribute_type": "INPUT",
                "data_type": "NPINPUT",
                "user_data":
                    {"value": None}
            },
            "Map":{
                "attribute_type": "INPUT",
                "data_type": "NPINPUT",
                "user_data":
                    {"value": 100}
            },
            "Planner":{
                "attribute_type": "INPUT",
                "data_type": "ENUM",
                "user_data":
                    {
                        "value": "ThetaStar",
                        "enum": ["AStar", "ThetaStar","Dijkstra","DStar","DStarLite","SThetaStar"]

                    }
            },
            "Path": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)
        self.automatic = False
        
    def func(self):
        # if self.data["Start"]["user_data"]["value"] is None or self.data["Target"]["user_data"]["value"] is None:
        #     return
        start = self.data["Start"]["user_data"]["value"]
        target = self.data["Target"]["user_data"]["value"]
        map = self.data["Map"]["user_data"]["value"]
        planner = self.data["Planner"]["user_data"]["value"]
        cls = getattr(pmp, planner)