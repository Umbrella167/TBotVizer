import multiprocessing
import pickle
import random
import time
from time import sleep

import tbkpy._core as tbkpy

# Define a global variable for the stop signal
stop_event = multiprocessing.Event()


def initialize_node(node, f):
    if f == 2:
        node = random.randint(0, 100)
    tbkpy.init(f"Node {node}")
    ep = tbkpy.EPInfo()
    ep.name = f"Node {node}"
    ep.msg_name = f"Node {node}_pub"
    ep.msg_type = "int"


def create_nodes(node_len):
    # 定义线程任务
    def initialize_node(node, f):
        node = 1
        if f == 2:
            node = random.randint(0, 100)
        tbkpy.init(f"Node {node}")
        ep = tbkpy.EPInfo()
        ep.name = f"Node {node}"
        ep.msg_name = f"Node {node}_pub"
        ep.msg_type = "int"

    puber = tbkpy.Publisher(ep)

    i = 1
    while i < 1000:
        i = i + random.randint(-10, 10)
        puber.publish(pickle.dumps(i))
        sleep(0.01)
        if stop_event.is_set():
            break


def create_nodes(node_len):
    # Create and start processes
    processes = []
    f = 2
    for node in range(node_len):
        process = multiprocessing.Process(target=initialize_node, args=(node, f))
        process.start()
        processes.append(process)
        if f == 2:
            sleep(3)

    return processes


# Stop all processes
def stop_all_nodes(processes):
    stop_event.set()
    for process in processes:
        process.join()


if __name__ == '__main__':
    processes = create_nodes(10)
    time.sleep(40)
    stop_all_nodes(processes)
