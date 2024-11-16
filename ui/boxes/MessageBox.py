import dearpygui.dearpygui as dpg
from ui.boxes import Box
from logger.Logger import Logger
import tbkpy._core as tbkpy
from utils.DataProcessor import tbk_data


class MessageBoxCallBack:
    def __init__(self):
        self.msg_subscriber_dict = {}

    def subscriber_msg(self, msg, msg_info):
        puuid, name, msg_name, msg_type, tree_item_tag_dict = msg_info
        value_checkbox_tag = tree_item_tag_dict["value_checkbox"]
        if dpg.get_value(value_checkbox_tag):
            dpg.configure_item(item=value_checkbox_tag, label=msg)
    


    def checkbox_record_msg(self, sender, app_data, user_data):
        is_checked = app_data
        msg_info, tree_item_tag_dict,box_tag  = user_data
        name = msg_info["name"]
        msg_name = msg_info["msg_name"]
        puuid = msg_info["puuid"]
        message_data = f"{puuid}_{name}:{msg_name}"
        msg_type = msg_info["msg_type"]
        msg_info["tag"] = box_tag

        if is_checked:
            if puuid not in self.msg_subscriber_dict:
                # 如果节点不在表内则添加该节点进表
                self.msg_subscriber_dict[puuid] = {}

            if msg_name not in self.msg_subscriber_dict[puuid]:
                # 如果消息不在表内，则添加消息进表
                self.msg_subscriber_dict[puuid][msg_name] = {}

            if name not in self.msg_subscriber_dict[puuid][msg_name]:
                # 如果消息不在表内则添加消息进表
                self.msg_subscriber_dict[puuid][msg_name][name] = tbk_data.Subscriber(
                    msg_info,
                    lambda msg: self.subscriber_msg(
                        msg, (puuid, name, msg_name, msg_type, tree_item_tag_dict)
                    ),
                )
        else:
            if puuid in self.msg_subscriber_dict:
                if msg_name in self.msg_subscriber_dict[puuid]:
                    if name in self.msg_subscriber_dict[puuid][msg_name]:
                        tbk_data.unsubscribe(msg_info)
                        del self.msg_subscriber_dict[puuid][msg_name][name]
                        del self.msg_subscriber_dict[puuid][msg_name]
                        dpg.configure_item(
                            item=tree_item_tag_dict["value_checkbox"], label=""
                        )


class MessageBox(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tags = None
        self.tree_tag = None
        self._callback = MessageBoxCallBack()
        self._logger = Logger()
        self.tree_item_tag_dict = {}
        self.tbk_data = tbk_data

    def create(self):
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="Message")
        with dpg.child_window(parent=self.tag) as self.msg_child_window_tag:
            # 添加列表头
            self.tree_tag = dpg.add_collapsing_header(label="Message List")
            # 插入树
            self.tags = self.insert_tree(self.tbk_data.message_tree["pubs"])

    def insert_tree(self, data):
        t_tree = []

        for puuid in data:
            # 添加节点列表
            node = dpg.add_tree_node(label=puuid, parent=self.tree_tag)
            t_node = []
            with dpg.table(parent=node, resizable=True) as table_sel_cols:
                dpg.add_table_column(label="Name", init_width_or_weight=0)
                dpg.add_table_column(label="LOG")
                dpg.add_table_column(label="Value")

                for uuid in data[puuid]:
                    msg_info = data[puuid][uuid].ep_info
                    node_name = msg_info.node_name
                    name = msg_info.name
                    msg_name = msg_info.msg_name
                    msg_type = msg_info.msg_type
                    msg_type_url = msg_info.msg_type_url
                    msg_info_dict = {
                        "msg_name": msg_name,
                        "name": name,
                        "msg_type": msg_type,
                        "uuid": uuid,
                        "puuid": puuid,
                    }
                    with dpg.table_row():
                        if puuid not in self.tree_item_tag_dict:
                            self.tree_item_tag_dict[puuid] = {}
                        if msg_name not in self.tree_item_tag_dict[puuid]:
                            self.tree_item_tag_dict[puuid][msg_name] = {}
                        if name not in self.tree_item_tag_dict[puuid][msg_name]:
                            self.tree_item_tag_dict[puuid][msg_name][name] = {}
                            # 订阅消息选择框
                            self.tree_item_tag_dict[puuid][msg_name][name][
                                "sub_checkbox"
                            ] = dpg.add_checkbox(
                                label=f"{msg_name}({name})",
                                callback=self._callback.checkbox_record_msg,
                                user_data=(
                                    msg_info_dict,
                                    self.tree_item_tag_dict[puuid][msg_name][name],
                                    self.tag
                                ),
                            )
                            # 记录消息选择框
                            self.tree_item_tag_dict[puuid][msg_name][name][
                                "log_checkbox"
                            ] = dpg.add_checkbox()

                            # 实时消息显示
                            self.tree_item_tag_dict[puuid][msg_name][name][
                                "value_checkbox"
                            ] = dpg.add_checkbox(default_value=True)

                    with dpg.drag_payload(
                        parent=self.tree_item_tag_dict[puuid][msg_name][name][
                            "sub_checkbox"
                        ],
                        payload_type="plot_data",
                        drag_data=msg_info_dict,
                    ):
                        dpg.add_text(f"{msg_name}({name})")
                t_tree.append(t_node)
        return t_tree

    # def insert_tree(self, data):
    #     t_tree = []
    #     for puuid in data:
    #         # 添加节点列表
    #         node = dpg.add_tree_node(label=puuid,parent=self.tree_tag)
    #         t_node = []
    #         for uuid in data[puuid]:
    #             msg_info = data[puuid][uuid].ep_info
    #             node_name = msg_info.node_name
    #             name = msg_info.name
    #             msg_name = msg_info.msg_name
    #             msg_type = msg_info.msg_type
    #             msg_type_url = msg_info.msg_type_url
    #             msg_info_dict = {
    #                 "msg_name": msg_name,
    #                 "name": name,
    #                 "msg_type": msg_type,
    #                 "uuid": uuid,
    #                 "puuid": puuid,
    #             }
    #             # 添加选框
    #             checkbox = dpg.add_checkbox(
    #                 label=f"{msg_name}({name})",
    #                 parent=node,
    #                 callback=self._callback.checkbox_record_msg,
    #                 user_data=(msg_info_dict, self._logger),
    #             )
    #             t_node.append(checkbox)
    #             # 设置拖拽
    #             with dpg.drag_payload(
    #                 parent=checkbox, payload_type="plot_data", drag_data=msg_info_dict
    #             ):
    #                 dpg.add_text(f"{puuid}_payload")
    #         t_tree.append(t_node)
    #     return t_tree

    def update(self):
        pass
