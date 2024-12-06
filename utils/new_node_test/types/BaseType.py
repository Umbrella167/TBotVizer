import dearpygui.dearpygui as dpg


class BaseType:
    width = 200

    def __init__(self, data, parent):
        self.name, self.info = data
        self.parent = parent
        self.is_output = False
        if self.info["attribute_type"] == "OUTPUT":
            self.is_output = True
        self.attr = dpg.add_node_attribute(
            attribute_type=dpg.mvNode_Attr_Output if self.is_output else dpg.mvNode_Attr_Input,
            parent=parent.tag,
            user_data=self.name
        )
