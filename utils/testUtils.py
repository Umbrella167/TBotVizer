import time
from time import sleep

import tbkpy._core as tbkpy
import tzcp.tbk.tbk_pb2 as tbkpb
import threading
import random

from twisted.plugin import pickle

# 结束信号
stop_event = threading.Event()


def create_nodes(node_len):
    NODE_LEN = 10

    # 定义线程任务
    def initialize_node(node):
        tbkpy.init(f"Node {node}")
        ep = tbkpy.EPInfo()
        ep.name = f"Node {node}"
        ep.msg_name = f"Node {node}_pub"
        ep.msg_type = "int"

        puber = tbkpy.Publisher(ep)

        # puber1 = tbkpy.Publisher(f"Node {node}", f"Node {node}_pub1")

        def f(msg):
            print(f"Node {node} received message: {msg}")

        i = 0
        while i<1000:
            f = -1
            i = i + random.randint(1, 10)*f
            puber.publish(pickle.dumps(i))
            sleep(0.01)
            while stop_event.is_set():
                break
            f = -f

        # suber = tbkpy.Subscriber(f"Node {node}", f"Node {node}_sub", f)


    # 创建并启动线程
    threads = []
    for node in range(NODE_LEN):
        thread = threading.Thread(target=initialize_node, args=(node,))
        thread.start()
        threads.append(thread)

    # # 等待所有线程完成
    # for thread in threads:
    #     thread.join()
    return threads


# 结束所有线程
def stop_all_nodes():
    stop_event.set()


if __name__ == '__main__':
    create_nodes(10)
    time.sleep(20)
    stop_all_nodes()
