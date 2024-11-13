from api.TBKApi import TBKApi
from utils.Utils import build_message_tree


class TBKData:
    def __init__(self, tbkapi: TBKApi):
        self.TBKApi = tbkapi
        self._param_data = self.TBKApi.get_param()
        self._message_data = self.TBKApi.get_message()
        self._message_node_tree = None

    def update(self):
        pass

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