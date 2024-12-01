import threading
import time

import dearpygui.dearpygui as dpg

from logger.logger import Logger
from ui.boxes.BaseBox import BaseBox
from utils.ClientLogManager import client_logger
from utils.DataProcessor import tbk_data


class MessageBox(BaseBox):
    only = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.header = None
        self.puuid_tags = {}
        self.table_tags = {}
        self.uuid_tags = {}
        self.create_time = None

        self.msg_logger = Logger("logs/msg_log")
        self._callback = MessageBoxCallBack(self.msg_logger)
        self.tree_item_tag_dict = {}
        self.tbk_data = tbk_data
        self.data = {}

    def create(self):
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="Message")
        self.header = dpg.add_collapsing_header(label="Message List", parent=self.tag)
        self.create_time = time.time()
        self.update()

    def update(self):
        if not (time.time() - self.create_time) % 2 < 0.01:
            # 每两秒更新一次数据
            return
        new_data = self.tbk_data.message_tree["pubs"]
        # 如果数据没有变化，则不更新
        if self.data == new_data:
            return
        # 然后处理节点的删除和新增
        current_puuids = set(self.data.keys())
        new_puuids = set(new_data.keys())
        # 找到需要删除的节点（即在current而不在new中的参数）
        puuids_to_delete = current_puuids - new_puuids
        # 找到需要新增的节点（即在new而不在current中的参数）
        puuids_to_add = new_puuids - current_puuids
        # 删除不需要的节点
        for puuid in puuids_to_delete:
            self.msg_logger.save()
            row_tag = self.puuid_tags[puuid]
            dpg.delete_item(row_tag)
            del self.puuid_tags[puuid]
        # 添加新增的节点
        for puuid in puuids_to_add:
            self.add_node(new_data, puuid)
        # 先更新现有的节点，检查行的变化
        for puuid in current_puuids.intersection(new_puuids):
            current_uuids = set(self.data[puuid].keys())
            new_uuids = set(new_data[puuid].keys())
            # 找到需要删除的行（即在current而不在new中的参数）
            uuids_to_delete = current_uuids - new_uuids
            # 找到需要新增的行（即在new而不在current中的参数）
            uuids_to_add = new_uuids - current_uuids
            # 删除多余的行
            for uuid in uuids_to_delete:
                row_tag = self.uuid_tags[uuid]
                dpg.delete_item(row_tag)
                del self.uuid_tags[uuid]
            # 添加新的行
            for uuid in uuids_to_add:
                self.add_row(new_data, puuid, uuid)
        client_logger.log("INFO", "MessageBox updated!")
        self.data = new_data.copy()

    def add_node(self, data, puuid):
        # 添加节点列表
        self.puuid_tags[puuid] = dpg.add_tree_node(label=puuid, parent=self.header)
        self.table_tags[puuid] = dpg.add_table(parent=self.puuid_tags[puuid], resizable=True)
        # 创建表标题
        dpg.add_table_column(label="Name", init_width_or_weight=0, parent=self.table_tags[puuid])
        dpg.add_table_column(label="LOG", parent=self.table_tags[puuid])
        dpg.add_table_column(label="Value", parent=self.table_tags[puuid])
        for uuid in data[puuid]:
            self.add_row(data, puuid, uuid)

    def add_row(self, data, puuid, uuid):
        # 添加行
        msg_info = data[puuid][uuid].ep_info
        name = msg_info.name
        msg_name = msg_info.msg_name
        msg_type = msg_info.msg_type
        msg_info_dict = {
            "msg_name": msg_name,
            "name": name,
            "msg_type": msg_type,
            "uuid": uuid,
            "puuid": puuid,
        }
        self.uuid_tags[uuid] = dpg.add_table_row(parent=self.table_tags[puuid])
        item_dict = (
            self.tree_item_tag_dict.setdefault(puuid, {})
            .setdefault(msg_name, {})
            .setdefault(name, {})
        )
        item_dict["sub_checkbox"] = dpg.add_checkbox(
            label=f"{msg_name}({name})",
            callback=self._callback.checkbox_record_msg,
            user_data=(msg_info_dict, item_dict, self.tag),
            parent=self.uuid_tags[uuid],
        )
        item_dict["log_checkbox"] = dpg.add_checkbox(parent=self.uuid_tags[uuid], )
        item_dict["value_checkbox"] = dpg.add_checkbox(
            default_value=True,
            parent=self.uuid_tags[uuid],
        )
        with dpg.drag_payload(
                parent=self.tree_item_tag_dict[puuid][msg_name][name][
                    "sub_checkbox"
                ],
                # payload_type="plot_data",
                drag_data=(msg_info_dict, item_dict),
        ):
            dpg.add_text(f"{msg_name}({name})")

    def destroy(self):
        self.msg_logger.close()
        super().destroy()
    # def insert_tree(self, data):
    #     for puuid in data:
    #         # 添加节点列表
    #         self.puuid_tags[puuid] = dpg.add_tree_node(label=puuid, parent=self.header)
    #         with dpg.table(parent=self.puuid_tags[puuid], resizable=True) as table_sel_cols:
    #             # 创建表标题
    #             dpg.add_table_column(label="Name", init_width_or_weight=0)
    #             dpg.add_table_column(label="LOG")
    #             dpg.add_table_column(label="Value")
    #
    #             for uuid in data[puuid]:
    #                 msg_info = data[puuid][uuid].ep_info
    #                 name = msg_info.name
    #                 msg_name = msg_info.msg_name
    #                 msg_type = msg_info.msg_type
    #                 msg_info_dict = {
    #                     "msg_name": msg_name,
    #                     "name": name,
    #                     "msg_type": msg_type,
    #                     "uuid": uuid,
    #                     "puuid": puuid,
    #                 }
    #                 with dpg.table_row():
    #                     item_dict = (
    #                         self.tree_item_tag_dict.setdefault(puuid, {})
    #                         .setdefault(msg_name, {})
    #                         .setdefault(name, {})
    #                     )
    #                     item_dict["sub_checkbox"] = dpg.add_checkbox(
    #                         label=f"{msg_name}({name})",
    #                         callback=self._callback.checkbox_record_msg,
    #                         user_data=(msg_info_dict, item_dict, self.tag),
    #                     )
    #                     item_dict["log_checkbox"] = dpg.add_checkbox()
    #                     item_dict["value_checkbox"] = dpg.add_checkbox(
    #                         default_value=True
    #                     )
    #
    #                 with dpg.drag_payload(
    #                         parent=self.tree_item_tag_dict[puuid][msg_name][name][
    #                             "sub_checkbox"
    #                         ],
    #                         payload_type="plot_data",
    #                         drag_data=(msg_info_dict, item_dict),
    #                 ):
    #                     dpg.add_text(f"{msg_name}({name})")


class MessageBoxCallBack:
    def __init__(self, msg_logger: Logger):
        self.msg_logger = msg_logger
        self.msg_subscriber_dict = {}
        self.lock = threading.Lock()

    def subscriber_msg(self, msg, msg_info):
        puuid, name, msg_name, msg_type, tree_item_tag_dict = msg_info
        value_checkbox_tag = tree_item_tag_dict["value_checkbox"]
        log_checkbox_tag = tree_item_tag_dict["log_checkbox"]
        if dpg.get_value(value_checkbox_tag):
            dpg.configure_item(item=value_checkbox_tag, label=msg)
        if dpg.get_value(log_checkbox_tag):
            with self.lock:
                self.msg_logger.record(msg, puuid, msg_name, name, msg_type)

    def checkbox_record_msg(self, sender, app_data, user_data):
        is_checked = app_data
        msg_info, tree_item_tag_dict, box_tag = user_data
        name = msg_info["name"]
        msg_name = msg_info["msg_name"]
        puuid = msg_info["puuid"]
        msg_type = msg_info["msg_type"]
        msg_info["tag"] = box_tag

        if is_checked:
            self.msg_subscriber_dict.setdefault(puuid, {}).setdefault(msg_name, {})[
                name
            ] = tbk_data.Subscriber(
                msg_info,
                lambda msg: self.subscriber_msg(
                    msg, (puuid, name, msg_name, msg_type, tree_item_tag_dict)
                ),
            )
            # tbk_data.Subscriber(
            #     msg_info,
            #     lambda msg: self.subscriber_msg(
            #         msg, (puuid, name, msg_name, msg_type, tree_item_tag_dict)
            #     ),
            # )
        else:
            if dpg.get_value(tree_item_tag_dict["log_checkbox"]):
                self.msg_logger.save()
            if puuid in self.msg_subscriber_dict and msg_name in self.msg_subscriber_dict[puuid]:
                if name in self.msg_subscriber_dict[puuid][msg_name]:
                    tbk_data.unsubscribe(msg_info, True)
                    # del self.msg_subscriber_dict[puuid][msg_name][name]
                    # del self.msg_subscriber_dict[puuid][msg_name]
                    # dpg.configure_item(
                    #     item=tree_item_tag_dict["value_checkbox"], label=""
                    # )
