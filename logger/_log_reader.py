from logger._logger_base import _LogReader

class LogReader:
    def __init__(self, log_package_path):
        """
        Initializes a LogReader to read logs from a specified log package path.

        :param log_package_path: The path to the log package to be read.
        """
        self.reader = _LogReader(log_package_path)

    def get_log_info(self):
        """
        Retrieves and prints information about the logs in the package, such as name, count, start timestamp, and end timestamp.

        :return: Information about the logs in the package.
        """
        return self.reader.get_log_info()
    def get_total_time(self):
        """
        Retrieves the total time span of the log package.

        :return: The total time span of the log package.
        """
        return self.reader.get_total_time()

    def read_logs(self):
        """
        Generator function to read logs from the opened log package.

        Usage Example:
        ```
        logger = Logger()
        log = logger.open()
        logs = log.read_logs()
        for log in logs:
            print(log)
        ```
        :return: Generator yielding log entries.
        """
        return self.reader.read_logs()
    @property
    def get_start_time(self):
        """
        Retrieves the start time of the log package.

        :return: The start time of the log package.
        """
        return self.reader.get_start_time()
    def get_msg_count(self):
        """
        Retrieves the total count of messages in the log package.

        :return: The count of messages in the log package.
        """
        return self.reader.get_msg_count()

    def select_msg(self, timestamp):
        """
        Selects a message based on a timestamp and returns an iterator for it.

        Usage Example:
        ```
        logger = Logger()
        log = logger.open()
        now_msg = log.select_msg(time.time() * 1e9)
        print(now_msg.msg())
        print(now_msg.next(step=1))
        print(now_msg.prev(step=1))
        ```
        :param timestamp: The timestamp to select the message by.
        :return: A message iterator for the selected message.
        """
        return self.reader.select_msg(timestamp)
    def read_log_by_timestamp(self, timestamp):
        """
        Reads a log based on a timestamp.

        Usage Example:
        ```
        logger = Logger()
        log = logger.open()
        log.read_log_by_timestamp(time.time() * 1e9)
        ```
        :param timestamp: The timestamp to read the log by.
        :return: The log entry.
        """
        return self.reader.read_log_by_timestamp(timestamp)
    def get_next_msg(self):
        """
        Retrieves the next message based on a timestamp.

        Usage Example:
        ```
        logger = Logger()
        log = logger.open()
        log.get_next_msg(time.time() * 1e9)
        ```
        :param timestamp: The timestamp to get the next message by.
        :return: The next message.
        """
        return self.reader.get_next_msg()
    
    def get_prev_msg(self):
        """
        Retrieves the previous message based on a timestamp.

        Usage Example:
        ```
        logger = Logger()
        log = logger.open()
        log.get_prev_msg(time.time() * 1e9)
        ```
        :param timestamp: The timestamp to get the previous message by.
        :return: The previous message.
        """
        return self.reader.get_prev_msg()
    
    @property   
    def is_open(self):
        """
        Checks if the log package is open for reading.

        :return: True if the log package is open, False otherwise.
        """
        return self.reader.is_open
    
    def filter(self, msg_name=None, name=None, msg_type=None, puuid=None, timestamp=None, index=None, count=None):
        """
        Filters the logs based on the provided criteria.

        Usage Example:
        ```
        logger = Logger()
        log = logger.open()
        log.filter(message_tag="vision", timestamp=0, index=0, count=10)
        log.filter(timestamp=[0, 99999999999999])
        ```
        :param message_tag: List of message tags to filter by (e.g., ["vision", "debug"]).
        :param timestamp: Either a specific timestamp or a range [start, end] to filter by.
        :param index: Either a specific index or a range [start, end] to filter by.
        :param count: Number of messages to return starting from the index.
        :return: List of filtered messages.
        """
        return self.reader.filter(msg_name, name, msg_type, puuid, timestamp, index, count)
