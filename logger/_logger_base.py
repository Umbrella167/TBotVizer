import os
from datetime import datetime
from time import time
import pickle
from tbkpy.socket.udp import UDPReceiver
import threading
import re
from datetime import datetime, timezone

from utils.ClientLogManager import client_logger


class UDPMultiCastReceiver(UDPReceiver):
    def __init__(
        self, group, port, *, bind_ip="", callback=None, user_data=None, plugin=None
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
        self.__callback(msg, self.user_data)

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
        for root, dirs, files in os.walk(dir):
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return size

    def get_log_packge(self, log_dir):
        """
        Retrieves a sorted list of log packages in the specified log directory.

        :param log_dir: The directory containing log packages.
        :return: A sorted list of log packages with their sizes.
        """
        directory_path = log_dir

        def extract_timestamp(file_name):
            match = re.search(
                r"Rec_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d+)", file_name
            )
            return (
                datetime.strptime(match.group(1), "%Y-%m-%d_%H-%M-%S-%f")
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
                if self.get_dir_size(os.path.join(directory_path, file)) > 0
            ]
            return sorted(
                log_files, key=lambda x: extract_timestamp(x[0]), reverse=True
            )
        except Exception as e:
            client_logger.log("ERROR", f"An error occurred: {e}")
            return []

    def get_log_files(self, log_packge_path):
        """
        Retrieves a list of log files within a specified log package.

        :param log_packge_path: The path of the log package.
        :return: A sorted list of log files.
        """
        try:
            files = [f for f in os.listdir(log_packge_path) if f.endswith(".log")]
            files.sort(key=lambda x: int(x.split("_")[0]))  # Sort by file index
            return files
        except Exception as e:
            client_logger.log("ERROR", f"Error retrieving log files: {e}")
            return []

class _LogDiskWriter:
    def __init__(self, output_dir="logs"):
        """
        A class responsible for writing logs to disk in a structured way.

        :param output_dir: The directory to store logs.
        """
        self.output_dir = output_dir
        self.chunking_size_len = 100
        self._file_max_size = 5 * 1024 * 1024  # 5MB
        self._current_file_index = 0
        self._current_file = None
        self._file_start_timestamp = None
        self._msg_index_file = 0
        self.data_list = []
        self.data_len = 0
        self.lock = threading.Lock()
        self.log_path_created = False
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        now = datetime.now()
        self.log_pack_dir = (
            now.strftime("Rec_%Y-%m-%d_%H-%M-%S-") + f"{now.microsecond}"
        )
        self.log_file_path = os.path.join(self.output_dir, self.log_pack_dir)

    def write(self, data):
        """
        Writes data to the log file, managing file chunks and size limits.

        :param data: The data to write.
        """
        with self.lock:
            if not self.log_path_created:
                if not os.path.exists(self.log_file_path):
                    os.mkdir(self.log_file_path)
                self.log_path_created = True

            self.data_list.append(data)
            self.data_len += 1
            self._msg_index_file += 1
            if self.data_len < self.chunking_size_len:
                return

            if (
                self._current_file is None
                or os.path.getsize(self._current_file.name) > self._file_max_size
            ):
                if self._current_file:
                    self._msg_index_file = 0
                    self._current_file.close()

                self._file_start_timestamp = int(time() * 1e9)
                file_name = (
                    f"{self._current_file_index}_{self._file_start_timestamp}.log"
                )
                self._current_file_index += 1
                file_path = os.path.join(self.log_file_path, file_name)
                try:
                    self._current_file = open(file_path, "ab")
                except Exception as e:
                    client_logger.log("ERROR", f"Error opening file {file_path}: {e}")
                    return

            try:
                pickle.dump(self.data_list, self._current_file)
                self._current_file.flush()
            except Exception as e:
                client_logger.log("ERROR", f"Error writing data to file: {e}")
            finally:
                self.data_list.clear()
                self.data_len = 0

    def close(self):
        """
        Closes the current log file.
        """
        with self.lock:
            if self._current_file:
                try:
                    self._current_file.close()
                except Exception as e:
                    client_logger.log("ERROR", f"Error closing file {e}")

class _LogReader:
    def __init__(self, log_package_path):
        """
        A class for reading and filtering logs from a specified log package.

        :param log_package_path: The path to the log package.
        """
        self._utils = _Utils()
        self.log_package_path = log_package_path
        self.selected_file = None

    def filter(self, message_tag=None, timestamp=None, index=None, count=None):
        """
        Filters the logs based on the provided criteria.

        :param message_tag: List of message tags to filter by (e.g., ["vision", "debug"]).
        :param timestamp: Either a specific timestamp or a range [start, end] to filter by.
        :param index: Either a specific index or a range [start, end] to filter by.
        :param count: Number of messages to return starting from the index.
        :return: List of filtered messages.
        """
        if not self.log_package_path:
            raise ValueError("No log package is currently opened or found.")

        filtered_messages = []

        # Read all logs and apply filters
        for entry in self.read_logs():
            if message_tag and entry["name"] not in message_tag:
                continue

            if timestamp:
                if isinstance(timestamp, list):
                    if not timestamp[0] <= entry["timestamp"] <= timestamp[1]:
                        continue
                else:
                    if entry["timestamp"] != timestamp:
                        continue

            if index:
                if isinstance(index, list):
                    if not index[0] <= entry["index"] <= index[1]:
                        continue
                else:
                    if entry["index"] != index:
                        continue

            filtered_messages.append(entry)

        # Apply count filter
        if count:
            if isinstance(count, list):
                start = count[0]
                end = count[1] if len(count) > 1 else len(filtered_messages)
                filtered_messages = filtered_messages[start:end]
            else:
                filtered_messages = filtered_messages[:count]

        return filtered_messages

    def get_log_info(self):
        """
        Prints information about each log entry, including name, count, start timestamp, and end timestamp.
        """
        if not self.log_package_path:
            raise ValueError("No log package is currently opened or found.")

        log_info = {}
        for entry in self.read_logs():
            name = entry["name"]
            timestamp = entry["timestamp"]

            if name not in log_info:
                log_info[name] = {
                    "count": 0,
                    "start_timestamp": timestamp,
                    "end_timestamp": timestamp,
                }

            log_info[name]["count"] += 1
            log_info[name]["end_timestamp"] = timestamp

            if timestamp < log_info[name]["start_timestamp"]:
                log_info[name]["start_timestamp"] = timestamp

        for name, info in log_info.items():
            start_ts_human = datetime.fromtimestamp(
                info["start_timestamp"] / 1e9, tz=timezone.utc
            )
            end_ts_human = datetime.fromtimestamp(
                info["end_timestamp"] / 1e9, tz=timezone.utc
            )

            # print(f"Name: {name}")
            # print(f"Count: {info['count']}")
            # print(f"Start Timestamp: {info['start_timestamp']:.0f} ({start_ts_human})")
            # print(f"End Timestamp: {info['end_timestamp']:.0f} ({end_ts_human})")
            # print()

    def read_logs(self, message_tag=None):
        """
        Generator to read and yield individual messages from log files.

        :param message_tag: The message tag to filter by.
        :yield: Each message entry that matches the filter.
        """
        if not self.log_package_path:
            raise ValueError("No log package is currently opened.")

        log_files = self._utils.get_log_files(self.log_package_path)
        for log_file in log_files:
            file_path = os.path.join(self.log_package_path, log_file)
            try:
                with open(file_path, "rb") as f:
                    while True:
                        try:
                            # Load a chunk of data from the log file
                            data_chunk = pickle.load(f)
                            for msg in data_chunk:
                                if message_tag is None or msg["name"] == message_tag:
                                    yield msg
                        except EOFError:
                            # Break the loop if end of file is reached
                            break
            except Exception as e:
                client_logger.log("ERROR", f"Error reading log file {file_path}: {e}")

    def get_closest_message(self, log_file_data, timestamp):
        """
        Finds the message closest to the specified timestamp in the log data.

        :param log_file_data: The log data to search within.
        :param timestamp: The target timestamp.
        :return: The closest message to the timestamp.
        """
        if not log_file_data:
            return None

        start_index = 0
        end_index = len(log_file_data) - 1

        # Handle cases where the timestamp is out of the range
        if timestamp <= log_file_data[start_index]["timestamp"]:
            return log_file_data[start_index]
        if timestamp >= log_file_data[end_index]["timestamp"]:
            return log_file_data[end_index]

        # Binary search to find the closest timestamp
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
        """
        Reads all messages from a specified log file.

        :param file_name: The name of the log file.
        :return: A list of all messages in the log file.
        """
        file_path = ""
        try:
            file_path = os.path.join(self.log_package_path, file_name)
            all_messages = []  # List to store all messages
            with open(file_path, "rb") as f:
                while True:
                    try:
                        # Load a chunk of data from the file
                        data_chunk = pickle.load(f)
                        # Add messages from the chunk to the total messages list
                        all_messages.extend(data_chunk)
                    except EOFError:
                        # Exit loop if end of file is reached
                        break
            return all_messages
        except Exception as e:
            client_logger.log("ErRoR", f"Error reading log file {file_path}: {e}")
            return []

    def read_log_by_timestamp(self, timestamp):
        """
        Reads a message by its timestamp.

        :param timestamp: The target timestamp to read.
        :return: The message closest to the timestamp.
        """
        sorted_filenames = self._utils.get_log_files(self.log_package_path)
        if not sorted_filenames:
            return

        # Check if the first file's timestamp is later than the given timestamp
        first_file_start_timestamp = int(
            sorted_filenames[0].split("_")[1].split(".")[0]
        )
        if first_file_start_timestamp > timestamp:
            self.selected_file = sorted_filenames[0]
            return self.read_log_file(sorted_filenames[0])[0]

        # Find the file containing the specified timestamp
        for filename in sorted_filenames:
            file_start_timestamp = int(filename.split("_")[1].split(".")[0])
            if file_start_timestamp <= timestamp:
                self.selected_file = filename
            else:
                break

        if not self.selected_file:
            return

        # Read content from the log file
        log_list = self.read_log_file(self.selected_file)
        return self.get_closest_message(log_list, timestamp)

    def select_msg(self, timestamp):
        """
        Selects a message based on a timestamp and returns an iterator for it.

        :param timestamp: The timestamp to select the message by.
        :return: A _LogIterator for the selected message.
        """
        msg = self.read_log_by_timestamp(timestamp)
        if not msg:
            return None
        msg_index_file = msg["index"]
        return _LogIterator(
            selected_file=self.selected_file,
            index=msg_index_file,
            msg=msg,
            log_reader=self,
        )

    def get_msg_count(self):
        """
        Retrieves the total count of messages in the log package.

        :return: The message count.
        """
        log_files = self._utils.get_log_files(self.log_package_path)[-1]

        last_msg = self.read_log_file(log_files)[-1]
        count = last_msg["count"]

        return count

class _LogIterator:
    def __init__(self, selected_file, index, msg, log_reader: _LogReader):
        """
        Iterator for traversing messages in a log file.

        :param selected_file: The currently selected file.
        :param index: The current index in the file.
        :param msg: The current message.
        :param log_reader: The log reader instance.
        """
        self.selected_file = selected_file
        self.current_msg = msg
        self.log_reader = log_reader
        self.current_index = index
        self.utils = _Utils()

    def _load_messages_from_file(self):
        """
        Helper function to load all messages from the current file.
        
        :return: All messages from the current file.
        """
        return self.log_reader.read_log_file(self.selected_file)

    def _update_file_and_index(self, file_index, new_index):
        """
        Helper function to update the selected file and index.

        :param file_index: The new file index.
        :param new_index: The new message index.
        """
        log_files = self.utils.get_log_files(self.log_reader.log_package_path)
        self.selected_file = log_files[file_index]
        self.current_index = new_index
        all_messages = self._load_messages_from_file()
        self.current_msg = all_messages[self.current_index]

    def next(self, step: int = 1):
        """
        Advance to the next message in the logs.

        :param step: The number of steps to move forward.
        :return: The next message, or None if at the end.
        """
        all_messages = self._load_messages_from_file()
        total_messages = len(all_messages)

        if self.current_index + step < total_messages:
            self.current_index += step
        else:
            log_files = self.utils.get_log_files(self.log_reader.log_package_path)
            current_file_index = int(self.selected_file.split("_")[0])
            next_file_index = current_file_index + 1

            if next_file_index < len(log_files):
                self._update_file_and_index(next_file_index, 0)
            else:
                return None

        self.current_msg = all_messages[self.current_index]
        return self.current_msg

    def prev(self, step: int = 1):
        """
        Move to the previous message in the logs.

        :param step: The number of steps to move backward.
        :return: The previous message, or None if at the beginning.
        """
        if self.current_index - step >= 0:
            self.current_index -= step
        else:
            log_files = self.utils.get_log_files(self.log_reader.log_package_path)
            current_file_index = int(self.selected_file.split("_")[0])
            prev_file_index = current_file_index - 1

            if prev_file_index >= 0:
                all_messages = self.log_reader.read_log_file(log_files[prev_file_index])
                self._update_file_and_index(prev_file_index, len(all_messages) - 1)
            else:
                return None

        self.current_msg = self._load_messages_from_file()[self.current_index]
        return self.current_msg

    def msg(self):
        """
        Return the current message.

        :return: The current message.
        """
        return self.current_msg

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

    def _new_msg(self, msg, tag, _from=""):
        """
        Creates a new message with metadata.

        :param msg: The message content.
        :param tag: The tag associated with the message.
        :param _from: The source of the message.
        :return: A dictionary representing the message.
        """
        self.msg_count += 1
        msgs = {
            "name": tag,
            "index": self._diskWriter._msg_index_file,
            "count": self.msg_count,
            "timestamp": int(time() * 1e9),
            "message": msg,
            "from": _from,
        }
        return msgs

    def record(self, msg, tag: str, _from: str = ""):
        """
        Records a message to the log.

        :param msg: The message content.
        :param tag: The tag associated with the message.
        :param _from: The source of the message.
        """
        new_msg = self._new_msg(msg, tag, _from)
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
        self.record(msg=msg[0], _from=msg[1], tag=user_data)

    def open(self, log_package_path=None):
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
                client_logger.log("ERRor", "No log package found.")
                return False, None
        return _LogReader(f"{self.log_dir}/{log_package_path}")

    def list_log_packge(self):
        """
        Lists all available log packages.

        :return: A list of log packages.
        """
        return self._utils.get_log_packge(self.log_dir)