import dearpygui.dearpygui as dpg

import ui.Theme as theme
import traceback
from collections import deque
import utils.Utils as utils
from api import TBKApi
from ui.box.MessageBox import MessageBox
from ui.box.ParamBox import ParamBox
from ui.Components import DiyComponents
from utils.DataProcessor import UiData, TBKData
from utils.CallBack import CallBack


class UI:
    def __init__(self, data: UiData, tbkapi: TBKApi.TBKApi):
        self._data = data
        self._tbkdata = TBKData(tbkapi)

        # self._tbkapi = tbkapi
        self._layout_manager = self._data.layout_manager
        self._diycomponents = DiyComponents(self._data)
        self._callback = CallBack(self._data, self._diycomponents)
        self._theme = theme
        self.maxlen = 5
        self.table_change_list = deque(maxlen=self.maxlen)

    def show_ui(self):
        self._layout_manager.load_layout()
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def create_viewport(self):
        self.create_global_handler()
        dpg.configure_app(
            docking=True,
            docking_space=True,
            init_file="dpg_layout.ini",
            load_init_file=True,
        )
        dpg.create_viewport(title="TBK-ParamManager", width=1920, height=1080)

    def run_loop(self, func=None):
        if func is not None:
            while dpg.is_dearpygui_running():
                func()
                dpg.render_dearpygui_frame()
        else:
            dpg.start_dearpygui()

    def create_param_window2(self):
        self.t_pbox = ParamBox(self._data, self._tbkdata)
        self.t_pbox.draw()

    # def create_param_window(self):
    #     with dpg.window(
    #         tag="param_window", label="Param", no_close=True, no_collapse=True
    #     ):
    #         self.create_param_table()

    # def create_param_table(self):
    #     dpg.delete_item("param_window", children_only=True)
    #     # 创建新的表格
    #     with dpg.table(
    #         header_row=True,
    #         policy=dpg.mvTable_SizingFixedFit,
    #         row_background=True,
    #         reorderable=True,
    #         resizable=True,
    #         no_host_extendX=False,
    #         hideable=True,
    #         borders_innerV=True,
    #         delay_search=True,
    #         borders_outerV=True,
    #         borders_innerH=True,
    #         borders_outerH=True,
    #         parent="param_window",
    #     ) as table_tag:
    #     # 添加表格列
    #         dpg.add_table_column(label="Param", width_fixed=True, parent=table_tag)
    #         dpg.add_table_column(label="Info", width_fixed=True, parent=table_tag)
    #         dpg.add_table_column(label="Type", width_fixed=True, parent=table_tag)
    #         dpg.add_table_column(label="Value", width_fixed=True, parent=table_tag)
    #         # table_tree = self._diycomponents.TableTree()
    #         # table_tree.build_dpg_tree(self._tbkdata.param_tree)
    #         # 添加表格行和内容
    #         for row_index, (param, value) in enumerate(self._tbkdata.param_data.items()):
    #             with dpg.table_row(parent=table_tag, tag=param):
    #                 dpg.add_text(default_value=param, tag=param + "_param")
    #                 _info = value["info"]
    #                 _type = value["type"]
    #                 for item in value:
    #                     if item == "value":
    #                         tag = param + "_" + item
    #                         self._diycomponents.param_input(
    #                             outer_instance=self._diycomponents,
    #                             data=self._uidata,
    #                             param=self._tbkdata,
    #                         ).new_input(
    #                             tag=tag,
    #                             value=value[item],
    #                             type=_type,
    #                             info=_info,
    #                             parent=param,
    #                         )
    #                         # 如果值是空的,那么设置为红色
    #                         if value[item] == "None":
    #                             self._diycomponents.set_input_color(tag, [255, 0, 0, 255])
    #                     else:
    #                         dpg.add_text(default_value=value[item], tag=param + "_" + item)

    def update_param_data2(self):
        self.t_pbox.update()

    # def update_param_data(self):
    #     change_param_data = self._tbkdata.param_change_data
    #     is_change = self._tbkdata.param_is_change
    #     if is_change:
    #         for change_type in change_param_data:
    #             if change_type == "added":
    #                 pass
    #             elif change_type == "removed":
    #                 pass
    #             elif change_type == "modified":
    #                 for param, _ in change_param_data[change_type].items():
    #                     attribute = dict(_["modified"].items())
    #                     attribute_type = list(attribute.keys())[0]
    #                     attribute_value = list(attribute.values())[0][0]
    #                     _type = self._tbkdata.param_data[param]["type"]
    #                     try:
    #                         _type = _type.lower()
    #                     except:
    #                         pass
    #                     # 获取参数类型
    #                     if attribute_type == "value":
    #                         # int类型
    #                         if _type in self._uidata.intname:
    #                             try:
    #                                 attribute_value = int(attribute_value)
    #                             except:
    #                                 attribute_value = 0
    #                         # float类型
    #                         elif _type in self._uidata.floatname:
    #                             try:
    #                                 attribute_value = float(attribute_value)
    #                             except:
    #                                 attribute_value = 0.0
    #                         # bool类型
    #                         elif _type in self._uidata.boolname:
    #                             attribute_value = attribute_value.lower()
    #                             attribute_value = (
    #                                 True if attribute_value == "true" else False
    #                             )
    #                         # str类型
    #                         else:
    #                             attribute_value = str(attribute_value)
    #                     else:
    #                         self.create_param_table()
    #                     try:
    #                         print(param + "_" + attribute_type)
    #                         dpg.set_value(param + "_" + attribute_type, attribute_value)
    #                     except Exception as e:
    #                         print(
    #                             f"ERROR(set_value): \n    Itme:{param}_{attribute_type}\n"
    #                         )
    #                     self.table_change_list.append(param + "_" + attribute_type)
    #
    #         # 逐渐改变颜色
    #         change_list_len = len(self.table_change_list)
    #         try:
    #             for i in range(change_list_len):
    #                 param = self.table_change_list[i]
    #                 if dpg.get_value(param) != "None":
    #                     self._diycomponents.set_input_color(
    #                         param, [0, 255 // (change_list_len - i), 0, 255]
    #                     )
    #                     if i == 0 and change_list_len == self.maxlen:
    #                         self._diycomponents.set_input_color(
    #                             param, [255, 255, 255, 255]
    #                         )
    #         except Exception as e:
    #             tb = traceback.extract_tb(e.__traceback__)
    #             file_name, line_number, func_name, text = tb[-1]
    #             print(
    #                 f"ERROR(set_input_color):\n    Item:{param} \n    File:{file_name}\n    Line:{line_number}\n    Function:{func_name}\n    Text:{text}"
    #             )

    def create_global_handler(self):
        with dpg.handler_registry() as global_hander:
            dpg.add_key_release_handler(callback=self._callback.on_key_release)
        # with dpg.item_handler_registry() as item_handler_registry:
        #     dpg.add_item_resize_handler(callback=self._callback.drawer_window_resize_callback)
        # dpg.bind_item_handler_registry("drawer_window", item_handler_registry)

    def create_message_window2(self):
        self.t_msgbox = MessageBox(self._data, self._tbkdata)
        self.t_msgbox.draw()

    # def create_message_window(self):
    #     with dpg.window(label="Message", tag="message_window"):
    #         self.create_message_list()

    # def create_message_list(self):
    #     message_data = self._tbkdata.message_data
    #     pubs = message_data["pubs"]
    #     with dpg.collapsing_header(label="Message List", tag = f"{dpg.generate_uuid()}_treenode"):
    #         item = []
    #         message_tree = utils.build_message_tree(pubs)
    #         for puuid, node_name in message_tree.items():
    #             for theme_name, node_msgs in node_name.items():
    #                 with dpg.tree_node(label=f"{theme_name}({puuid})",tag = f"{dpg.generate_uuid()}_treenode"):
    #                     for publisher, messages in node_msgs.items():
    #                         with dpg.tree_node(label=publisher,tag= f"{dpg.generate_uuid()}_treenode"):
    #                             for msg in messages:
    #                                 with dpg.group(tag=f"{dpg.generate_uuid()}_group",horizontal=True):
    #                                     uuid = dpg.generate_uuid()
    #                                     dpg.add_checkbox(label=msg,tag=f"{uuid}_checkbox",callback=self._callback.check_message,user_data=(msg,uuid))
    #                                     dpg.add_spacer(width=80)
    #                                     dpg.add_text(tag=f"{uuid}_text",default_value="")

    # def create_message_view(self):
    #     with dpg.window(label="Message View", tag="message_view"):
    #         with dpg.drawlist():
    #             pass

    # puuid -> node_name -> name -> msg_name

    def update_message_list2(self):
        self.t_msgbox.update()
        pass

    # def update_message_list(self):
    #     change_message_data = self._tbkapi.message_change_data
    #     is_change = self._tbkapi.message_is_change
    #     if is_change:
    #         for change_type in change_message_data:
    #             if change_type == "added":
    #                 pass
    #             elif change_type == "removed":
    #                 pass
    #             elif change_type == "modified":
    #                 pass

    # def create_message_draw_window(self):
