from utils.ClientLogManager import client_logger
import importlib

def try_import(module_path, class_name):
    try:
        client_logger.log("TRACE", f"Trying to import {class_name} from {module_path}")
        # 如果 class_name 为 "*"，导入模块中所有内容
        if class_name == "*":
            module = importlib.import_module(module_path)  # 导入整个模块
            client_logger.log("TRACE", f"Successfully imported all from {module_path}")
            return module  # 返回模块对象
        # 如果 class_name 为具体类名，尝试从模块中导入指定类
        elif class_name is not None:
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        # 如果 class_name 为 None，跳过导入
        else:
            client_logger.log("TRACE", f"Skipping import for {module_path} as class_name is None")
            return None
    except ImportError as e:
        client_logger.log("ERROR", f"Failed to import {class_name} from {module_path}", e)
        return None
    except Exception as e:
        client_logger.log("ERROR", f"Unexpected error while importing {class_name} from {module_path}", e)
        return None


# 列出所有需要动态导入的模块路径和类名
modules_to_import = [
    ("ui.boxes.BaseBox", "BaseBox"),
    ("ui.boxes.ConsoleBox", "ConsoleBox"),
    ("ui.boxes.InputConsoleBox", "InputConsoleBox"),
    ("ui.boxes.MessageBox", "MessageBox"),
    ("ui.boxes.ParamBox", "ParamBox"),
    ("ui.boxes.PlotVzBox", "PlotVzBox"),
    ("ui.boxes.LogReaderBox", "LogReaderBox"),
    ("ui.boxes.NodeBox", "NodeBox"),
    ("ui.boxes.IMUBox", "IMUBox"),
    ("ui.boxes.PointsCouldBox", "PointsCouldBox"),
    ("ui.boxes.RRTBox", "RRTBox"),
    # ("ui.boxes.FastLioBox", "FastLioBox"),
    ("ui.boxes.PointsFaceBox", "PointsFaceBox"),
    ("ui.boxes.AGV", "*"),  # 改为 "*" 表示导入模块中所有内容
]

# 动态导入模块，绑定到全局作用域
for module_path, class_name in modules_to_import:
    imported = try_import(module_path, class_name)
    if imported:
        if class_name and class_name != "*":
            globals()[class_name] = imported  # 将类名绑定到全局作用域
        elif class_name == "*":
            module_name = module_path.split('.')[-1]
            globals()[module_name] = imported  # 将模块绑定到全局作用域