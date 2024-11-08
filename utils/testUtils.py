import time
import tbkpy._core as tbkpy
import threading

# 结束信号
stop_event = threading.Event()


def create_nodes(node_len):
    NODE_LEN = 10

    # 定义线程任务
    def initialize_node(node):
        tbkpy.init(f"Node {node}")
        puber = tbkpy.Publisher(f"Node {node}", f"Node {node}_pub")

        # puber1 = tbkpy.Publisher(f"Node {node}", f"Node {node}_pub1")

        def f(msg):
            print(f"Node {node} received message: {msg}")

        suber = tbkpy.Subscriber(f"Node {node}", f"Node {node}_sub", f)
        while not stop_event.is_set():
            time.sleep(1)  # 示例任务循环

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
    time.sleep(60)
    stop_all_nodes()
