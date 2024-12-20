import tbkpy._core as tbkpy

from api.TBKApi import TBKApi
from config.SystemConfig import TBK_NODE_NAME
from utils.ClientLogManager import client_logger


class UiData:
    def __init__(self):
        self.draw_mouse_pos = (0, 0)
        self.draw_mouse_pos_last = (0, 0)
        self.mouse_move_pos = (0, 0)
ui_data = UiData()


class TBKData:
    def __init__(self):
        self.tbk_api = TBKApi()
        self._param_data = None
        self._message_data = None
        self._message_node_tree = None
        self.callback_dict = {}
        self.subscriber_dict = {}

    def update(self):
        pass

    def unsubscribe(self, info: dict, is_del_msg=False):
        puuid = info["puuid"]
        name = info["name"]
        msg_name = info["msg_name"]
        tag = info["tag"]

        if tag in self.callback_dict.get(puuid, {}).get(msg_name, {}).get(name, {}):
            del self.callback_dict[puuid][msg_name][name][tag]

        if len(self.callback_dict[puuid][msg_name][name]) < 1 or is_del_msg:
            del self.subscriber_dict[puuid][msg_name][name]
            del self.callback_dict[puuid][msg_name][name]

    def is_subscribed(self, info: dict) -> bool:
        return info["name"] in self.subscriber_dict.get(info["puuid"], {}).get(info["msg_name"], {})

    def callback_manager(self, msg, info):
        puuid = info["puuid"]
        name = info["name"]
        msg_name = info["msg_name"]

        for tag in self.callback_dict.get(puuid, {}).get(msg_name, {}).get(name, {}):
            callback = (
                self.callback_dict.get(puuid, {})
                .get(msg_name, {})
                .get(name, {})
                .get(tag)
            )
            if callback:
                callback(msg)

    def Subscriber(self, info: dict, callback):
        puuid = info["puuid"]
        name = info["name"]
        msg_name = info["msg_name"]
        tag = info["tag"]
        if "user_data" in info:
            user_data = info["user_data"]
        self.callback_dict.setdefault(puuid, {}).setdefault(msg_name, {}).setdefault(
            name, {}
        )[tag] = callback

        if self.subscriber_dict.get(puuid, {}).get(msg_name, {}).get(name) is not None:
            # 如果self.subscriber_dict[puuid][msg_name][name]中有值则退出
            return
        client_logger.log("INFO", f"Add new subscriber({puuid}, {msg_name}, {name})")
        self.subscriber_dict.setdefault(puuid, {}).setdefault(msg_name, {})[name] = (
            tbkpy.Subscriber(
                # puuid, #这个属性tbk内还没开出接口
                name,
                msg_name,
                lambda msg: self.callback_manager(msg, info),
            )
        )

    @property
    def param_data(self):
        # self._old_param_data = self._param_data
        self._param_data = self.tbk_api.get_param()
        return self._param_data

    @property
    def message_data(self):
        # self._old_message_data = self._message_data
        self._message_data = self.tbk_api.get_message()
        return self._message_data

    def put_param(self, param, value):
        self.tbk_api.put_param(param, value)

    @property
    def message_tree(self):
        message_tree = {}
        for node_type in self.message_data:
            tree = {}
            if node_type == "ps":
                continue
            elif node_type == "subs":
                continue
            elif node_type == "pubs":
                data = self.message_data[node_type]
                for uuid in data:
                    node_name = data[uuid].ep_info.node_name
                    if node_name == TBK_NODE_NAME:
                        puuid = node_name
                    else:
                        puuid = f"{node_name}_{data[uuid].puuid}"
                    if puuid not in tree:
                        tree[puuid] = {}
                    tree[puuid][uuid] = data[uuid]
            else:
                client_logger.log("ERROR", f"{self.__class__} build message_tree type error!")
            message_tree[node_type] = tree
        return message_tree

# tbk_data = TBKData()

class MsgSubscriberManager:
    def __init__(self):
        self.subscriber_data = {}

    def add_subscriber(self, puuid: str, msg_name: str, name: str, item_tag: str, subscriber):
        """
        添加订阅者到嵌套字典中。
        """
        # 使用 `setdefault` 简化嵌套字典的初始化
        self.subscriber_data.setdefault(puuid, {}).setdefault(msg_name, {}).setdefault(name, {})[item_tag] = subscriber
    def remove_subscriber(self, puuid: str, msg_name: str, name: str, item_tag: str):
        """
        删除嵌套字典中的订阅者。
        """
        # 检查是否存在对应的订阅者
        if puuid in self.subscriber_data and msg_name in self.subscriber_data[puuid]:
            if name in self.subscriber_data[puuid][msg_name] and item_tag in self.subscriber_data[puuid][msg_name][name]:
                del self.subscriber_data[puuid][msg_name][name][item_tag]  # 删除具体的 item_tag
                # 如果 name 下没有任何订阅者，则删除 name
                if not self.subscriber_data[puuid][msg_name][name]:
                    del self.subscriber_data[puuid][msg_name][name]
                # 如果 msg_name 下没有任何订阅者，则删除 msg_name
                if not self.subscriber_data[puuid][msg_name]:
                    del self.subscriber_data[puuid][msg_name]
                # 如果 puuid 下没有任何消息，则删除 puuid
                if not self.subscriber_data[puuid]:
                    del self.subscriber_data[puuid]
                return True
        return False  # 如果订阅者不存在，则返回 False

    def clear(self):
        """
        清空所有订阅者。
        """
        for puuid, msg_names in self.subscriber_data.items():
            for msg_name, names in msg_names.items():
                for name, item_tags in names.items():
                    for item_tag, subscriber in item_tags.items():
                        tbk_data.unsubscribe({"puuid": puuid, "msg_name": msg_name, "name": name, "tag": item_tag})
        self.subscriber_data.clear()