import dearpygui.dearpygui as dpg
from ui.boxes import Box
from logger.Logger import Logger
class MessageBoxCallBack:
    def __init__(self):
        self.subscriber_list = {}
        pass
    def checkbox_record_msg(self, sender, app_data, user_data):
        msg_info,logger = user_data
class MessageBox(Box):
    def __init__(self, tbk_data, **kwargs):
        super().__init__(**kwargs)
        self.tags = None
        self.tree_tag = None
        self.tbk_data = tbk_data
        self._callback = MessageBoxCallBack()
        self._logger = Logger()
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
            node = dpg.add_tree_node(label=puuid)
            t_node = []
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
                    "puuid": puuid
                }
                # 添加选框
                checkbox = dpg.add_checkbox(label=f"{msg_name}({name})", parent=node,callback=self._callback.checkbox_record_msg, user_data=(msg_info_dict,self._logger))
                t_node.append(checkbox)
                # 设置拖拽
                with dpg.drag_payload(parent=checkbox, payload_type="plot_data", drag_data=msg_info_dict):
                    dpg.add_text(f"{puuid}_payload")
            t_tree.append(t_node)
        return t_tree


    def update(self):
        pass