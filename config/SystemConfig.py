import time

ENVIRONMENT = 'development'


class Config:
    CURRENT_LANGUAGE = "zh"
    TBK_NODE_NAME = "TBK-Client"
    FONT_FILE = "static/font/BLACK-NORMAL.ttf"
    # FONT_FILE = "static/font/SmileySans-Oblique.ttf"
    # FONT_FILE = "static/font/Minecraft.ttf"
    # FONT_FILE = "static/font/FiraCode-Regular.ttf"
    LOG_DIR = "logs/ui_logs"


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


configurations = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

config = configurations[ENVIRONMENT]
run_time = time.time()
PROHIBITED_BOXES = ["ConsoleBox", "InputConsoleBox"]
