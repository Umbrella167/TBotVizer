import time
from time import sleep

import tbkpy._core as tbkpy
import tzcp.tbk.tbk_pb2 as tbkpb
import threading
import random

import pickle

# 结束信号
stop_event = threading.Event()


def create_nodes(node_len):
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
        f = -1
        while i < 1000:
            i = i + random.randint(1, 10) * f
            puber.publish(pickle.dumps(i))
            f = -f
            sleep(0.01)
            if stop_event.is_set():
                break

        # suber = tbkpy.Subscriber(f"Node {node}", f"Node {node}_sub", f)

    # 创建并启动线程
    threads = []
    for node in range(node_len):
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
    time.sleep(40)
    stop_all_nodes()
