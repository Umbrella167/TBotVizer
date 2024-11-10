from api.TBKApi import TBKApi


class TBKData:
    def __init__(self, tbkapi: TBKApi):
        self._TBKApi = tbkapi
        self._param_data = self._TBKApi.get_param()
        self._message_data = self._TBKApi.get_message()

    def update(self):
        pass
        # self._param_data = self._TBKApi.get_param()
        # self._message_data = self._TBKApi.get_message()

    @property
    def param_data(self):
        self._old_param_data = self._param_data
        self._param_data = self._TBKApi.get_param()
        return self._param_data

    @property
    def message_data(self):
        self._old_message_data = self._message_data
        self._message_data = self._TBKApi.get_message()
        return self._message_data

    def put_param(self, param, value):
        self._TBKApi.put_param(param, value)
