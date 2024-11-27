import os
import pickle
import re
import threading
from collections import defaultdict
from datetime import datetime
from time import time
from zipfile import ZipFile, ZIP_STORED

from tbkpy.socket.udp import UDPReceiver

from utils.ClientLogManager import client_logger


class UDPMultiCastReceiver(UDPReceiver):
    def __init__(
            self,
            group,
            port,
            *,
            bind_ip="",
            callback=None,
            user_data=None,
            plugin=None,
    ):
        """
        Initializes a UDP multicast receiver that listens to a specified group and port.

        :param group: The multicast group to join.
        :param port: The port to listen on.
        :param bind_ip: The IP address to bind to. Defaults to "".
        :param callback: The callback function to invoke when a message is received.
        :param user_data: Additional user data to pass to the callback.
        :param plugin: Plugin to be used, if any.
        """
        self.user_data = user_data
        self.__callback = callback
        super().__init__(
            port,
            multicast=True,
            multicast_group=group,
            bind_ip=bind_ip,
            callback=self.callback_udp,
            plugin=None,
        )

    def callback_udp(self, msg):
        """
        Callback function that is called when a UDP message is received.

        :param msg: The received message.
        """
        self.__callback(
            msg,
            self.user_data,
        )


class _Utils:
    def __init__(self):
        """
        Utility class providing helper functions for file and log management.
        """
        pass

    def get_dir_size(self, dir):
        """
        Calculates the total size of a directory, including its subdirectories and files.

        :param dir: The directory path.
        :return: Total size in bytes.
        """
        size = 0
        for (
                root,
                dirs,
                files,
        ) in os.walk(dir):
            size += sum(
                [
                    os.path.getsize(
                        os.path.join(
                            root,
                            name,
                        )
                    )
                    for name in files
                ]
            )
        return size

    def get_log_packge(self, log_dir):
        """
        Retrieves a sorted list of log packages in the specified log directory.

        :param log_dir: The directory containing log packages.
        :return: A sorted list of log packages with their sizes.
        """
        directory_path = log_dir

        def extract_timestamp(
                file_name,
        ):
            match = re.search(
                r"Rec_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d+)",
                file_name,
            )
            return (
                datetime.strptime(
                    match.group(1),
                    "%Y-%m-%d_%H-%M-%S-%f",
                )
                if match
                else None
            )

        try:
            log_files = [
                (
                    file,
                    f"{(self.get_dir_size(os.path.join(directory_path, file)) / (1024 * 1024)):.2f}MB",
                )
                for file in os.listdir(directory_path)
                if self.get_dir_size(
                    os.path.join(
                        directory_path,
                        file,
                    )
                )
                   > 0
            ]
            return sorted(
                log_files,
                key=lambda x: extract_timestamp(x[0]),
                reverse=True,
            )
        except Exception as e:
            client_logger.log("error", e)
            return []

    def get_log_files(self, log_package_path):
        """
        Retrieves a list of log files within a specified log package (ZIP file).

        :param log_package_path: The path of the log package.
        :return: A sorted list of log files.
        """
        try:
            if type(log_package_path).__name__ != "str":
                log_package_path = log_package_path.filename

            with ZipFile(log_package_path, "r") as zip_file:

                # List all files in the zip that end with '.log'
                files = [f for f in zip_file.namelist() if f.endswith(".log")]
                # Sort files based on the index extracted from the filename

                files.sort(key=lambda x: int(x.split("_")[0]))  # Sort by file index
                return files
        except Exception as e:
            client_logger.log("error", f"{e},get_log_files error")
            return []


class _LogDiskWriter:
    def __init__(self, output_dir="logs"):
        self.output_dir = output_dir
        self.chunking_size_len = 100000
        self._current_file_index = 0
        self._file_start_timestamp = None
        self._msg_index_file = 0
        self.data_list = []
        self.data_len = 0
        self.lock = threading.Lock()
        self.log_path_created = False
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        now = datetime.now()
        self.log_pack_dir = now.strftime("Rec_%Y-%m-%d_%H-%M-%S-") + f"{now.microsecond}"
        self.zip_file_path = os.path.join(self.output_dir, f"{self.log_pack_dir}.tzlog")
        self._zip_file = None

    def write(self, data):
        if not self.log_path_created:
            self._zip_file = ZipFile(self.zip_file_path, "a", ZIP_STORED)
            self.log_path_created = True
        self.data_list.append(data)
        self.data_len += 1
        self._msg_index_file += 1
        if self.data_len < self.chunking_size_len:
            return

        self._save_to_file()

    def save_current_data(self):
        self._save_to_file()

    def _save_to_file(self):
        self._msg_index_file = 0
        if not self.data_list:
            return
        self._file_start_timestamp = self.data_list[0]["timestamp"]
        file_name = f"{self._current_file_index}_{self._file_start_timestamp}.log"
        self._current_file_index += 1

        try:
            with self.lock:
                with self._zip_file.open(file_name, "w") as log_file:
                    pickle.dump(self.data_list, log_file)
        except Exception as e:
            client_logger.log("error", e)
        finally:
            print("clear")

            self.data_list.clear()
            self.data_len = 0

    def close(self):
        if self._zip_file:
            try:
                self._zip_file.close()
            except Exception as e:
                client_logger.log("error", e)


class _LogReader:
    def __init__(self, log_package_path):
        self._utils = _Utils()
        self.log_package_path = log_package_path
        self.selected_file = None
        self.zip_file = None
        self.now_msg = None
        self.now_msg_list = None
        # Open the zip file
        try:
            if os.path.exists(self.log_package_path):
                self.zip_file = ZipFile(self.log_package_path, "r")
        except:
            client_logger.log("error", "Path Error")

    @property
    def is_open(self):
        return self.zip_file is not None

    def get_log_info(self):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened or found.")
            raise ValueError("No log package is currently opened or found.")
        log_info = defaultdict(int)
        for entry in self.read_logs():
            puuid = entry["puuid"]
            msg_name = entry["msg_name"]
            name = entry["name"]
            msg_type = entry["msg_type"]
            key = (puuid, msg_name, name, msg_type)
            log_info[key] += 1

        for (puuid, msg_name, name, msg_type), count in log_info.items():
            client_logger.log(
                "info", f"PUUID: {puuid}, MSG NAME: {msg_name}, MSG_TYEP: {msg_type}, NAME: {name}, COUNT: {count}"
            )
        return log_info

    def get_start_time(self):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened.")
            raise ValueError("No log package is currently opened.")
        log_files = self._utils.get_log_files(self.zip_file)
        start_log_file = log_files[0]
        start_log_file_data = self.read_log_file(start_log_file)
        start_log_file_timestamp = start_log_file_data[0]["timestamp"]
        return start_log_file_timestamp

    def read_logs(self, message_tag=None):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened.")
            raise ValueError("No log package is currently opened.")
        log_files = self._utils.get_log_files(self.zip_file)
        for log_file in log_files:
            try:

                with self.zip_file.open(log_file, "r") as f:
                    while True:
                        try:
                            data_chunk = pickle.load(f)
                            for msg in data_chunk:
                                if message_tag is None or msg["name"] == message_tag:
                                    yield msg
                        except EOFError:
                            break
            except Exception as e:
                client_logger.log("error", e)

    def get_closest_message(self, log_file_data, timestamp):
        if not log_file_data:
            return None

        start_index = 0
        end_index = len(log_file_data) - 1

        if timestamp <= log_file_data[start_index]["timestamp"]:
            return log_file_data[start_index]
        if timestamp >= log_file_data[end_index]["timestamp"]:
            return log_file_data[end_index]

        while start_index < end_index:
            mid_index = (start_index + end_index) // 2
            mid_timestamp = log_file_data[mid_index]["timestamp"]

            if mid_timestamp == timestamp:
                return log_file_data[mid_index]
            elif mid_timestamp < timestamp:
                start_index = mid_index + 1
            else:
                end_index = mid_index

        closest_index = start_index
        if start_index > 0:
            prev_index = start_index - 1
            if abs(log_file_data[prev_index]["timestamp"] - timestamp) <= abs(
                    log_file_data[start_index]["timestamp"] - timestamp
            ):
                closest_index = prev_index

        return log_file_data[closest_index]

    def read_log_file(self, file_name):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened.")

            raise ValueError("No log package is currently opened.")

        try:
            all_messages = []
            with self.zip_file.open(file_name, "r") as f:
                while True:
                    try:
                        data_chunk = pickle.load(f)
                        all_messages.extend(data_chunk)
                    except EOFError:
                        break
            return all_messages
        except Exception as e:
            client_logger.log("error", e)
            return []

    def get_total_time(self):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened.")
            raise ValueError("No log package is currently opened.")

        log_files = self._utils.get_log_files(self.zip_file)
        start_log_file = log_files[0]
        start_log_file_data = self.read_log_file(start_log_file)
        start_log_file_timestamp = start_log_file_data[0]["timestamp"]
        last_log_file = log_files[-1]
        last_log_file_data = self.read_log_file(last_log_file)
        last_log_file_timestamp = last_log_file_data[-1]["timestamp"]
        total_time = last_log_file_timestamp - start_log_file_timestamp
        return total_time / 1e9

    def read_log_by_timestamp(self, timestamp):
        if not self.zip_file:
            return
        sorted_filenames = self._utils.get_log_files(self.zip_file)
        if not sorted_filenames:
            return

        first_file_start_timestamp = int(sorted_filenames[0].split("_")[1].split(".")[0])
        if first_file_start_timestamp > timestamp:
            self.selected_file = sorted_filenames[0]
            self.now_msg = self.read_log_file(sorted_filenames[0])[0]
            return self.now_msg

        for filename in sorted_filenames:
            file_start_timestamp = int(filename.split("_")[1].split(".")[0])
            if file_start_timestamp <= timestamp:
                self.selected_file = filename
            else:
                break

        if not self.selected_file:
            return

        self.now_msg_list = self.read_log_file(self.selected_file)

        self.now_msg = self.get_closest_message(self.now_msg_list, timestamp)
        return self.now_msg

    def get_msg_count(self):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened.")
            raise ValueError("No log package is currently opened.")

        log_files = self._utils.get_log_files(self.zip_file)[-1]
        last_msg = self.read_log_file(log_files)[-1]
        count = last_msg["count"]

        return count

    def get_next_msg(self):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened.")
            raise ValueError("No log package is currently opened.")

        if not self.selected_file:
            client_logger.log("error", "No file is currently selected.")
            raise ValueError("No file is currently selected.")
        if not self.now_msg:
            client_logger.log("error", "No message is currently selected.")
            raise ValueError("No message is currently selected.")

        if not self.now_msg_list:
            self.now_msg_list = self.read_log_file(self.selected_file)

        msg_list_count = len(self.now_msg_list)

        index = self.now_msg["index"]
        next_index = index + 1
        if next_index > msg_list_count - 1:
            next_index = 0
            next_file_index = int(self.selected_file.split("_")[0]) + 1
            log_files = self._utils.get_log_files(self.zip_file)
            if next_file_index > len(self._utils.get_log_files(self.zip_file)) - 1:
                return None
            next_file_name = log_files[next_file_index]
            self.selected_file = next_file_name
            self.now_msg_list = self.read_log_file(next_file_name)
        self.now_msg = self.now_msg_list[next_index]
        return self.now_msg

    def get_prev_msg(self):
        if not self.zip_file:
            client_logger.log("error", "No log package is currently opened.")
            raise ValueError("No log package is currently opened.")

        if not self.selected_file:
            client_logger.log("error", "No file is currently selected.")
            raise ValueError("No file is currently selected.")
        if not self.now_msg:
            client_logger.log("error", "No message is currently selected.")
            raise ValueError("No message is currently selected.")

        if not self.now_msg_list:
            self.now_msg_list = self.read_log_file(self.selected_file)

        index = self.now_msg["index"]
        previous_index = index - 1

        # If the previous index is less than 0, go to the previous file
        if previous_index < 0:
            previous_file_index = int(self.selected_file.split("_")[0]) - 1
            log_files = self._utils.get_log_files(self.zip_file)
            if previous_file_index < 0:
                return None  # No previous message available
            previous_file_name = log_files[previous_file_index]
            self.selected_file = previous_file_name
            self.now_msg_list = self.read_log_file(previous_file_name)
            previous_index = len(self.now_msg_list) - 1

        self.now_msg = self.now_msg_list[previous_index]
        return self.now_msg


class _Logger:
    def __init__(self, log_dir="logs"):
        """
        Logger class that manages recording and reading logs, including UDP messages.

        :param log_dir: The directory to store logs.
        """
        self.log_dir = log_dir
        self._diskWriter = _LogDiskWriter(self.log_dir)
        self._utils = _Utils()
        self.udp_reciver = {}
        self.msg_count = 0
        self.is_recording = False
        self.lock = threading.Lock()

    def record_udp(self, udp_dict: dict):
        """
        Records UDP messages based on a dictionary of UDP configurations.

        :param udp_dict: A dictionary with configurations for each UDP message.
        """
        for msg in udp_dict:
            self.udp_reciver[msg] = UDPMultiCastReceiver(
                udp_dict[msg][0],
                udp_dict[msg][1],
                callback=self.udp_callback,
                user_data=msg,
            )

    def _new_msg(
            self,
            msg: str,
            puuid: str,
            msg_name: str,
            name: str,
            msg_type: str,
    ):

        """
        Creates a new message with metadata.

        :param msg: The message content.
        :param tag: The tag associated with the message.
        :param _from: The source of the message.
        :return: A dictionary representing the message.
        """
        msg = {
            "message": msg,
            "name": name,
            "msg_name": msg_name,
            "puuid": puuid,
            "index": self._diskWriter._msg_index_file,
            "count": self.msg_count,
            "timestamp": int(time() * 1e9),
            "msg_type": msg_type,
        }
        self.msg_count += 1

        return msg

    def record(
            self,
            msg,
            puuid: str,
            msg_name: str,
            name: str,
            msg_type: str,
    ):
        """
        Records a message to the log.

        :param msg: The message content.
        :param tag: The tag associated with the message.
        :param _from: The source of the message.
        """
        self.is_recording = True
        new_msg = self._new_msg(
            msg,
            puuid,
            msg_name,
            name,
            msg_type,
        )
        self._diskWriter.write(new_msg)

    def stop(self):
        """
        Stops recording UDP messages and clears the receiver list.
        """
        for obj in self.udp_reciver:
            self.udp_reciver[obj].stop()
        self.udp_reciver.clear()

    def udp_callback(self, msg, user_data):
        """
        Callback function for recording UDP messages.

        :param msg: The UDP message content.
        :param user_data: Additional user data associated with the UDP message.
        """
        self.record(
            msg=msg[0],
            _from=msg[1],
            tag=user_data,
        )

    def open(
            self,
            log_package_path=None,
    ):
        """
        Opens a log package for reading.

        :param log_package_path: The path to the log package. If None, opens the latest package.
        :return: A tuple of success status and the log reader instance.
        """
        if log_package_path is None:
            log_package_path = self.list_log_packge()
            if log_package_path:
                log_package_path = log_package_path[0][0]
            else:
                client_logger.log(
                    "ERRor",
                    "No log package found.",
                )
                return (
                    False,
                    None,
                )
        return _LogReader(f"{self.log_dir}/{log_package_path}")

    def list_log_packge(self, dir=None):
        """
        Lists all available log packages.

        :return: A list of log packages.
        """
        if dir == None:
            dir = self.log_dir
        return self._utils.get_log_packge(dir)
