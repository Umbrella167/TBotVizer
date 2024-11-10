from main import tbk_data
from utils.testUtils import create_nodes, stop_all_nodes
import tzcp.tbk.tbk_pb2 as tbkpb

def test_attr():
    pass
    # tLIST = ("ip", "puuid", "pid", "uuid", "msg_name", "name", "node_name", "node_ns", "ns", "subs")
    #
    # create_nodes(5)
    # message_data = tbk_data.message_data
    # pubs = message_data["pubs"]
    # # message_tree = build_message_tree(pubs)
    #
    # for k,v in pubs.items():
    #     print("k:", k)
    #
    #     print("v:", v.__slots__)
    #     # slots = getattr(v.__slots__)
    #     for attr in tLIST:
    #         value = getattr(v, attr, None)
    #         print(f"{attr} {value}")



    # print(message_tree)
    # stop_all_nodes()
    # for puuid, node_name in message_tree.items():
    #     for theme_name, node_msgs in node_name.items():
    #         with dpg.tree_node(label=f"{theme_name}({puuid})", tag=f"{puuid}_treenode"):
    #             for publisher, messages in node_msgs.items():
    #                 with dpg.tree_node(label=publisher, tag=f"{puuid}_{publisher}_treenode"):
    #                     for msg in messages:
    #                         pass

    # for field in fields(attr_obj.__class__):
    #     print(f"{field.name} = {getattr(attr_obj, field.name)}")



def test_answer():
    # create_nodes(5)
    # api = TBKApi.TBKApi()
    # print(api.param_tree)
    # stop_all_nodes()
    pass
