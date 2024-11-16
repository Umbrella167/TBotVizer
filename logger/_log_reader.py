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

    def filter(self, message_tag=None, timestamp=None, index=None, count=None):
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
        return self.reader.filter(message_tag, timestamp, index, count)
