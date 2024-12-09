import dearpygui.dearpygui as dpg


class BaseType:
    width = 200

    def __init__(self, name, info, parent):
        self.name = name
        self.info = info
        self.parent = parent
        self.is_output = None
        attribute_type = dpg.mvNode_Attr_Static
        if self.info["attribute_type"] == "OUTPUT":
            self.is_output = True
            attribute_type = dpg.mvNode_Attr_Output
        elif self.info["attribute_type"] == "INPUT":
            self.is_output = False
            attribute_type = dpg.mvNode_Attr_Input

        self.tag = dpg.add_node_attribute(
            attribute_type=attribute_type,
            parent=parent.tag,
            user_data=self.name
        )

    def update(self):
        pass
