from ui.boxes.BaseBox import Box
import dearpygui.dearpygui as dpg

class NodeBox(Box):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collapsing_header = None
        self.group = None
        self.node_editor = None

    def create(self):
        self.check_and_create_window()
        # if self.label is None:
        #     dpg.configure_item(self.tag, label="NodeBox")
        with dpg.group(horizontal=True,parent=self.tag):
            with dpg.child_window(width=100) as self.collapsing_header_tag:
                dpg.add_collapsing_header(label="MMMMM")
            with dpg.child_window():
                with dpg.node_editor(
                        callback=lambda sender, app_data: dpg.add_node_link(app_data[0], app_data[1], parent=sender),
                        delink_callback=lambda sender, app_data: dpg.delete_item(app_data),
                        minimap=True,
                        minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                ):
                    with dpg.node(label="Node 1", pos=[10, 10]):
                        with dpg.node_attribute():
                            dpg.add_input_float(label="F1", width=150)

                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                            dpg.add_input_float(label="F2", width=150)

                    with dpg.node(label="Node 2", pos=[300, 10]):
                        with dpg.node_attribute() as na2:
                            dpg.add_input_float(label="F3", width=200)

                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                            dpg.add_input_float(label="F4", width=200)

                    with dpg.node(label="Node 3", pos=[25, 150]):
                        with dpg.node_attribute():
                            dpg.add_input_text(label="T5", width=200)
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                            dpg.add_simple_plot(label="Node Plot", default_value=(0.3, 0.9, 2.5, 8.9), width=200, height=80,
                                                histogram=True)

        # item_auto_resize(self.collapsing_header_tag,self.tag,0,0.15)