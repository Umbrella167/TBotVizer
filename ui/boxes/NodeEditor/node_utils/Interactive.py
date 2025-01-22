from ui.boxes.NodeEditor.node_utils.BaseNode import BaseNode


class Input(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "": {"attribute_type": "OUTPUT", "data_type": "MULTILINEINPUT", "user_data": {"value": None}},
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)

    # def func(self):
    #     if not self.done:
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 self.done = True