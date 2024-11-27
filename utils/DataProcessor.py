from api.TBKApi import TBKApi
from utils.ClientLogManager import client_logger
import tbkpy._core as tbkpy


class UiData:
    def __init__(self):
        self.draw_mouse_pos = (0, 0)
        self.draw_mouse_pos_last = (0, 0)
        self.mouse_move_pos = (0, 0)


class TBKData:
    def __init__(self, tbkapi: TBKApi):
        self.TBKApi = tbkapi
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
        self._param_data = self.TBKApi.get_param()
        return self._param_data

    @property
    def message_data(self):
        # self._old_message_data = self._message_data
        self._message_data = self.TBKApi.get_message()
        return self._message_data

    def put_param(self, param, value):
        self.TBKApi.put_param(param, value)

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
                    puuid = f"{data[uuid].ep_info.node_name}_{data[uuid].puuid}"
                    if puuid not in tree:
                        tree[puuid] = {}
                    tree[puuid][uuid] = data[uuid]
            else:
                client_logger.log("ERROR", f"{self.__class__} build message_tree type error!")
            message_tree[node_type] = tree
        return message_tree


ui_data = UiData()
tbk_api = TBKApi()
tbk_data = TBKData(tbk_api)
