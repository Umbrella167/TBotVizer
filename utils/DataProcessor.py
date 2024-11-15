from api.TBKApi import TBKApi
from utils.Utils import build_message_tree
import tbkpy._core as tbkpy


class UiData:
    def __init__(self):
        self.draw_mouse_pos = (0, 0)
        self.draw_mouse_pos_last = (0, 0)
        self.mouse_move_pos = (0, 0)


class TBKData:
    def __init__(self, tbkapi: TBKApi):
        self.TBKApi = tbkapi
        self._param_data = self.TBKApi.get_param()
        self._message_data = self.TBKApi.get_message()
        self._message_node_tree = None
        self.callback_dict = {}
        self.subscriber_list = []

    def update(self):
        pass

    def callback_manager(self, msg,info):
        puuid = info["puuid"]
        name = info["name"]
        msg_name = info["msg_name"]
        tag = info["tag"]
        if "user_data" in info:
            user_data = info["user_data"]

        if puuid in self.callback_dict:
            if msg_name in self.callback_dict[puuid]:
                if name in self.callback_dict[puuid][msg_name]:
                    if tag in self.callback_dict[puuid][msg_name][name]:
                        self.callback_dict[puuid][msg_name][name][tag](msg)

    def Subscriber(self, info: dict, callabck):
        puuid = info["puuid"]
        name = info["name"]
        msg_name = info["msg_name"]
        tag = info["tag"]
        if "user_data" in info:
            user_data = info["user_data"]

        if puuid not in self.callback_dict:
            self.callback_dict[puuid] = {}
        if msg_name not in self.callback_dict[puuid]:
            self.callback_dict[puuid][msg_name] = {}
        if name not in self.callback_dict[puuid][msg_name]:
            self.callback_dict[puuid][msg_name][name] = {}
        self.callback_dict[puuid][msg_name][name][tag] = callabck
        self.subscriber_list.append(
            tbkpy.Subscriber(
                # puuid, #这个属性tbk内还没开出接口
                name,
                msg_name,
                lambda msg:self.callback_manager(msg,info),
            )
        )
        print(111)
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
        if self._message_node_tree is None:
            self._message_node_tree = {}
            for type in self._message_data:
                tree = {}
                if type == "ps":
                    continue
                elif type == "subs":
                    continue
                elif type == "pubs":
                    data = self._message_data[type]
                    for uuid in data:
                        puuid = f"{data[uuid].ep_info.node_name}_{data[uuid].puuid}"
                        if puuid not in tree:
                            tree[puuid] = {}
                        tree[puuid][uuid] = data[uuid]
                else:
                    print(f"{self.__class__} build message_tree type error!")
                self._message_node_tree[type] = tree
        return self._message_node_tree


ui_data = UiData()
tbk_data = TBKData(TBKApi())