from api import TBKApi
from utils.DataProcessor import TBKData
from utils.Utils import build_message_tree
from utils.testUtils import create_nodes, stop_all_nodes

def test_attr():
    tbk_api = TBKApi.TBKApi()
    tbk_data = TBKData(tbk_api)
    create_nodes(5)

    # original_param = tbk_api.get_original_param()
    # for k, v in original_param.items():
    #     print(k, '  |  ', v)


    message = tbk_data.message_node_tree

    print(message)
    # unpack_and_print(message)

    stop_all_nodes()


def unpack_and_print(d, indent=0):
    for key, value in d.items():
        print('\n  ' * indent + str(key) + ':', end=' ')
        if isinstance(value, dict):
            print('>>>')
            unpack_and_print(value, indent + 1)
        else:
            print(value)
    # message_data = tbk_data.message_data
    # pubs = message_data["pubs"]
    # # message_node_tree = build_message_tree(pubs)
    #
    # for k,v in pubs.items():
    #     print("k:", k)
    #
    #     print("v:", v.__slots__)
    #     # slots = getattr(v.__slots__)
    #     for attr in tLIST:
    #         value = getattr(v, attr, None)
    #         print(f"{attr} {value}")




def test_answer():
    # create_nodes(5)
    # api = TBKApi.TBKApi()
    # print(api.param_tree)
    # stop_all_nodes()
    pass
