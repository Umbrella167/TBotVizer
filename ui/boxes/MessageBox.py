import dearpygui.dearpygui as dpg
from ui.boxes import Box


class MessageBox(Box):
    def __init__(self, tbk_data, **kwargs):
        super().__init__(**kwargs)
        self.tags = None
        self.tree_tag = None
        self.tbk_data = tbk_data
        if self.label is None:
            dpg.configure_item(self.tag, label="Message")

    def create(self):
        # 添加列表头
        self.tree_tag = dpg.add_collapsing_header(label="Message List", parent=self.tag)
        # 插入树
        self.tags = self.insert_tree(self.tbk_data.message_tree["pubs"])


    def insert_tree(self, data):
        t_tree = []
        for puuid in data:
            # 添加节点列表
            node = dpg.add_tree_node(label=puuid, parent=self.tree_tag)
            t_node = []
            for uuid in data[puuid]:
                msg_info = data[puuid][uuid].ep_info
                node_name = msg_info.node_name
                name = msg_info.name
                msg_name = msg_info.msg_name
                msg_type = msg_info.msg_type
                msg_type_url = msg_info.msg_type_url
                user_data = {
                    "msg_name": msg_name,
                    "name": name,
                    "msg_type": msg_type,
                    "uuid": uuid,
                    "puuid": puuid
                }
                # 添加选框
                checkbox = dpg.add_checkbox(label=f"{msg_name}({name})", parent=node)
                t_node.append(checkbox)
                # 设置拖拽
                with dpg.drag_payload(parent=checkbox, payload_type="plot_data", drag_data=user_data):
                    dpg.add_text(f"{puuid}_payload")
            t_tree.append(t_node)
        return t_tree


    def update(self):
        pass
        # dpg.does_alias_exist()

        # message_data = self.tbk_data.message_data
        # pubs = message_data["pubs"]
        # message_node_tree = utils.build_message_tree(pubs)
        # for puuid, node_name in message_node_tree.items():
        #     dpg.configure_item(label=publisher,tag=f"{dpg.generate_uuid()}_treenode")
        #     # print(dpg.get_item_configuration(f"{puuid}_treenode"))

        # message_data = self.tbk_data.message_data
        # pubs = message_data["pubs"]
        # item = []
        # message_node_tree = utils.build_message_tree(pubs)
        # for puuid, node_name in message_node_tree.items():
        #     for theme_name, node_msgs in node_name.items():
        #         print(f"{puuid}_treenode:", dpg.get_item_configuration(f"{puuid}_treenode"))
        #         for publisher, messages in node_msgs.items():
        #             # f"{puuid}_{publisher}_treenode"
        #             print(f"{puuid}_{publisher}_treenode:", dpg.get_item_configuration(f"{puuid}_{publisher}_treenode"))
        #
        #             for msg in messages:
        #                 # f"{puuid}_{publisher}_{msg}_group"
        #                 print(f"{puuid}_{publisher}_{msg}_group", dpg.get_item_configuration(f"{puuid}_{publisher}_{msg}_group"))
        #
        #                 uuid = f"{puuid}_{publisher}_{msg}_group"
        #                 # print(uuid)
        #                 dpg.set_item_user_data(f"{uuid}_checkbox", (msg, uuid))

        # dpg.add_spacer(_width=80)
        # dpg.add_text(tag=f"{uuid}_text", default_value="")

        # exit(0)

        # message_data = self.tbk_data.message_data
        # pubs = message_data["pubs"]
        # with dpg.collapsing_header(label="Message List", tag=f"{dpg.generate_uuid()}_treenode"):
        #     item = []
        #     message_node_tree = utils.build_message_tree(pubs)
