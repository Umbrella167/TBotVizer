from loguru import logger
import os

from config.SystemConfig import config


class ClientLogManager:
    def __init__(self, log_file="ui_logs.log"):
        # TRACE：用于追踪代码中的详细信息。
        # DEBUG：用于调试和开发过程中的详细信息。
        # INFO：用于提供一般性的信息，表明应用程序正在按预期运行。
        # SUCCESS：用于表示成功完成的操作。
        # WARNING：用于表示潜在的问题或警告，不会导致应用程序的中断或错误。
        # ERROR：用于表示错误，可能会导致应用程序的中断或异常行为。
        # CRITICAL：用于表示严重错误，通常与应用程序无法继续执行相关。
        self.logger = logger
        self.log_dir = config.LOG_DIR
        self.log_file = log_file
        self.log_levels = ["trace", "debug", "info", "success", "warning", "error", "critical"]

        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 配置日志
        logger.add(
            os.path.join(self.log_dir, log_file),
            rotation="00:00",
            retention="7 days",
            compression="zip"
        )

    def log(self, level, msg, no=None):
        if level.lower() in self.log_levels:
            self.logger.log(level.upper(), msg)
        else:
            if no is not None:
                self.logger.level(level.upper(), no=no)
                self.logger.log(level.upper(), msg)
            self.logger.error("Unknown log level: {}".format(level))


client_logger = ClientLogManager()
