from api import TBKApi
from utils.DataProcessor import TBKData
from utils.testUtils import create_nodes, stop_all_nodes


def test_attr():
    tbk_api = TBKApi.TBKApi()
    tbk_data = TBKData(tbk_api)
    create_nodes(5)

    # original_param = tbk_api.get_original_param()
    # for k, v in original_param.items():

    message = tbk_data.message_node_tree

    stop_all_nodes()


def test_answer():
    # create_nodes(5)
    # api = tbk_api.tbk_api()
    # stop_all_nodes()
    pass
