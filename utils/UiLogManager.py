from loguru import logger
import os

from config.SystemConfig import config


class UiLogManager:
    def __init__(self, log_file='ui_log_{time}.log'):
        self.logger = logger
        self.log_dir = config.LOG_DIR
        self.log_file = log_file
        self.log_levels = ['debug', 'info', 'warning', 'error', 'critical']
        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 配置日志
        logger.add(
            os.path.join(self.log_dir, log_file),
            rotation="1 day",
            retention="7 days",
            compression="zip"
        )

    def info(self, message):
        self.logger.info(message)


