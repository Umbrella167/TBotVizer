from logger._logger_base import _Logger
from logger._log_reader import LogReader
class Logger:
    def __init__(self, log_dir="logs"):
        """
        Logger class for managing log recording and reading, including UDP messages.

        :param log_dir: The directory to store logs.
        """
        self.logger = _Logger(log_dir)

    def record_udp(self, udp_dict):
        """
        Records UDP messages based on a dictionary of UDP configurations.

        Usage Example:
        ```
        udp_dict = {
            "event": ["233.233.233.233", 1670],
            "vision": ["233.233.233.233", 41001],
            "debug": ["233.233.233.233", 20001],
        }

        logger = Logger()
        logger.record_udp(udp_dict)
        while True:
            pass
        ```
        :param udp_dict: A dictionary with configurations for each UDP message.
        """
        self.logger.record_udp(udp_dict)

    def stop(self):
        """
        Stops recording UDP messages and clears the receiver list.
        """
        self.logger.stop()

    def record(self, message,puuid, msg_name, name,msg_type):
        """
        Records a message to the log with a specified tag and source.

        Usage Example:
        ```

        logger = Logger()

        while True:
            message = "msg"
            logger.record(message, tag="vision")
        ```
        :param message: The message content to record.
        :param tag: The tag associated with the message.
        :param source: The source of the message.
        """
        self.logger.record(message, puuid, msg_name, name,msg_type)

    def list_log_packages(self):
        """
        Lists all available log packages in the log directory and prints them.

        :return: A list of log packages.
        """
        packge = self.logger.list_log_packge()
        print(packge)
        return packge

    def open(self, log_package_path=None):
        """
        Opens a log package for reading. If no path is specified, opens the latest package.

        :param log_package_path: The path to the log package. If None, the latest package is opened.
        :return: An instance of LogReader for the opened log package.
        """
        if log_package_path is None:
            log_package_path = self.logger.list_log_packge()
            if log_package_path:
                log_package_path = log_package_path[0][0]
            else:
                print("No log package found.")
                return None
        return LogReader(f"{self.logger.log_dir}/{log_package_path}")

if __name__ == "__main__":

    udp_dict = {
        "event": ["233.233.233.233", 1670],
        "vision": ["233.233.233.233", 41001],
        "debug": ["233.233.233.233", 20001],
    }
