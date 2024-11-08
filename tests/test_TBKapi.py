from api import TBKApi
from utils.testUtils import create_nodes, stop_all_nodes


def test_answer():
    create_nodes(5)
    api = TBKApi.TBKApi()
    print(api.param_tree)
    stop_all_nodes()
