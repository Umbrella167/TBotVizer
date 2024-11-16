import os
import json
import time
import threading
from datetime import datetime
import log_pb2
import socket

class Logger:
    def __init__(self, output_dir='logs'):
        """
        初始化日志记录器，设置日志文件路径和头部信息。
        """
        now = datetime.now()
        self.lock = threading.Lock()
        self.previous_log_message = None
        # 创建日志文件名，包含日期和时间
        log_file_name = now.strftime("Rec_%Y-%m-%d_%H-%M-%S-") + f"{now.microsecond}.log"
        self.output_dir = output_dir
        self.log_file_name = log_file_name
        self.log_file_path = os.path.join(self.output_dir, self.log_file_name)
        self.log_file = log_pb2.LogFile()
        self.log_file.header.CopyFrom(self.create_log_file_header())

        # 如果输出目录不存在，则创建
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 打开日志文件进行追加写入
        self.file = open(self.log_file_path, 'ab')
        # 如果文件为空，则写入头部信息
        if os.stat(self.log_file_path).st_size == 0:
            self.save_log_header()


    def __del__(self):
        """
        销毁日志记录器对象时关闭文件句柄。
        """
        self.file.close()

    def save_all_logs(self):
        """
        保存所有日志消息到文件。
        """
        print("Saving all log messages...")
        for log_message in self.log_file.messages:
            self.save_log(log_message)
        print("All log messages saved.")

    def save_log(self, log_message):
        """
        保存单条日志消息到文件。
        """
        with self.lock:
            serialized_log_message = log_message.SerializeToString()
            # 写入消息的长度，确保每次读取时可以区分消息边界
            self.file.write(len(serialized_log_message).to_bytes(4, 'big'))
            self.file.write(serialized_log_message)
            self.file.flush()

    def save_log_header(self):
        """
        保存日志文件的头部信息到文件。
        """
        with self.lock:
            # 序列化头部信息并写入文件
            serialized_header = self.log_file.header.SerializeToString()
            self.file.write(len(serialized_header).to_bytes(4, 'big'))
            self.file.write(serialized_header)
            self.file.flush()

    def create_log_message(self, message_type, message_data):
        """
        创建日志消息。
        """
        log_message = log_pb2.LogMessage()
        log_message.timestamp = int(time.time() * 1e9)  # 当前时间戳，单位为纳秒
        log_message.message_type = message_type
        log_message.version = 1

        if message_type == log_pb2.MessageType.MESSAGE_JSON:
            log_message.json_data = json.dumps(message_data)
            log_message.message_size = len(log_message.json_data)
        else:
            if isinstance(message_data, bytes):
                log_message.message_data = message_data
            else:
                log_message.message_data = message_data.SerializeToString()
            log_message.message_size = len(log_message.message_data)
        return log_message

    def create_log_file_header(self):
        """
        创建日志文件头部信息。
        """
        log_file_header = log_pb2.LogFileHeader()
        log_file_header.file_type = "TBK_LOG"
        log_file_header.format_version = 1
        log_file_header.checksum = "None"
        return log_file_header

    def log(self, message_data, message_type=log_pb2.MessageType.MESSAGE_PROTO, save_module="RealTime", size=0, energy_saving=False):
        """
        记录日志消息,根据不同的保存模块选择不同的保存策略.
            实时保存 (RealTime) 立即保存日志消息到文件.
            手动保存 (Manual) 将日志消息添加到消息列表,稍后手动保存.
            分块保存 (Chunking) 将日志消息添加到消息列表,当消息列表达到指定大小时保存所有消息并清空列表.
            节能模式 (EnergySaving) 检查当前消息是否与上一次消息相同，如果相同则不保存.
        """
        MOUDLE = ["RealTime", "Manual", "Chunking"]
        # 创建当前日志消息
        log_message = self.create_log_message(message_type, message_data)

        # 节能模式检查
        if energy_saving and self.previous_log_message is not None:
            print(self.previous_log_message.message_data)
            if log_message.message_data == self.previous_log_message.message_data:
                return

        if save_module == MOUDLE[0]:  # 实时保存
            self.log_file.messages.append(log_message)  # 添加到日志文件的消息列表中
            self.log_file.SerializeToString()
            self.save_log(log_message)
        elif save_module == MOUDLE[1]:  # 手动保存
            self.log_file.messages.append(log_message)  # 添加到日志文件的消息列表中
            self.log_file.SerializeToString()
        elif save_module == MOUDLE[2] and size > 0:  # 分块保存
            self.log_file.messages.append(log_message)  # 添加到日志文件的消息列表中
            if len(self.log_file.messages) >= size:
                self.save_all_logs()
                self.log_file.Clear()
        else:
            pass

        # 更新前一条日志消息
        self.previous_log_message = log_message

        def log_udp(self,port,ip = "127.0.0.1", message_type=log_pb2.MessageType.MESSAGE_PROTO, save_module="RealTime", size=0):
            """
            记录从 UDP 接收的数据。
            """
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((ip, port))
            data, addr = sock.recvfrom(65535)
            self.log(data, message_type, save_module,size)

        
class LogPlayer:
    def __init__(self, log_path):

        self.log_path = log_path
        self.log_file = None
        self.current_index = 0
        self.file_handle = open(self.log_path, 'rb')  # 打开日志文件
        self.read_header()  # 读取并解析头部信息

    def read_header(self):
        """
        读取并解析日志文件的头部信息。
        """
        start_time = time.time()
        length_bytes = self.file_handle.read(4)  # 读取头部长度
        if not length_bytes:
            raise RuntimeError("Log file is empty or corrupted")
        header_length = int.from_bytes(length_bytes, 'big')
        header_bytes = self.file_handle.read(header_length)  # 读取头部内容
        self.log_file_header = log_pb2.LogFileHeader()
        self.log_file_header.ParseFromString(header_bytes)  # 解析头部内容

    def get_log_header(self):
        """
        返回日志文件的头部信息。
        """
        return self.log_file_header

    def get_next_message(self):
        """
        返回日志文件中的下一条消息。
        """
        def read_exact(f, num_bytes):
            data = f.read(num_bytes)
            if len(data) != num_bytes:
                raise RuntimeError("Unexpected end of file")
            return data

        # 读取消息长度
        length_bytes = self.file_handle.read(4)
        if not length_bytes:
            raise IndexError("No more messages in log file")  # 若无更多消息，抛出IndexError
        message_length = int.from_bytes(length_bytes, 'big')

        # 读取实际的日志消息
        message_bytes = read_exact(self.file_handle, message_length)
        log_message = log_pb2.LogMessage()
        log_message.ParseFromString(message_bytes)
        return log_message

    def play_log(self):
        """
        生成器函数，逐条返回日志文件中的消息。
        """
        while True:
            try:
                yield self.get_next_message()
            except IndexError:
                break

    def read_log(self, wait_time=10):
        """
        一次性读取并解析整个日志文件。
        """
        def read_exact(f, num_bytes):
            """
            帮助函数，用于精确读取指定数量的字节，否则抛出错误。
            """
            data = f.read(num_bytes)
            if len(data) != num_bytes:
                raise RuntimeError("Unexpected end of file")
            return data

        start_time = time.time()
        log_file = log_pb2.LogFile()

        with open(self.log_path, 'rb') as f:
            # 读取并解析头部信息
            length_bytes = read_exact(f, 4)
            header_length = int.from_bytes(length_bytes, 'big')
            header_bytes = read_exact(f, header_length)
            log_file.header.ParseFromString(header_bytes)

            while True:
                if time.time() - start_time > wait_time:
                    raise TimeoutError("Reading log file took too long")

                # 读取消息长度
                length_bytes = f.read(4)
                if not length_bytes:
                    break
                message_length = int.from_bytes(length_bytes, 'big')

                # 读取实际的日志消息
                message_bytes = read_exact(f, message_length)
                log_message = log_pb2.LogMessage()
                log_message.ParseFromString(message_bytes)
                log_file.messages.append(log_message)

        return log_file
    def get_message_count(self):
        """
        返回日志文件中的消息数量。
        """
        count = 0
        with open(self.log_path, 'rb') as f:
            # 读取并跳过头部信息
            length_bytes = f.read(4)
            if not length_bytes:
                return count
            header_length = int.from_bytes(length_bytes, 'big')
            f.read(header_length)
            while True:
                # 读取消息长度
                length_bytes = f.read(4)
                if not length_bytes:
                    break
                message_length = int.from_bytes(length_bytes, 'big')
                
                # 跳过实际的日志消息
                f.read(message_length)
                count += 1
        return count
    def __del__(self):
        self.file_handle.close()

