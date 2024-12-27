def try_import(module_path, class_name=None):
    """
    动态尝试导入模块和类，支持单个模块或模块中的特定类。

    :param module_path: 模块路径
    :param class_name: 要导入的类名，如果为 None，则导入整个模块
    :return: 导入的模块或类；如果导入失败则返回 None
    """
    try:
        if class_name:
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        else:
            return __import__(module_path)
    except ImportError as e:
        print(f"Failed to import {class_name or module_path}: {e}")
        return None


# 定义需要导入的模块和类
modules_to_import = [
    ("utils.node_utils.BaseNode", "BaseNode"),
    ("utils.node_utils.Math", None),  # 导入整个模块（Math 中的所有内容）
    ("utils.node_utils.Map", "Map"),
    ("utils.node_utils.Interactive", None),  # 导入整个模块（Interactive 中的所有内容）
    ("utils.node_utils.RandomInt", "RandomInt"),
    ("utils.node_utils.AGVControl", "AGVControl"),
    ("utils.node_utils.Astar", "AStarNode"),
    ("utils.node_utils.PID", "PositionalPID"),
    ("utils.node_utils.ParseIMU", "ParseIMU"),
    ("utils.node_utils.TBKNode", None),  # 导入整个模块（TBKNode 中的所有内容）
    ("utils.node_utils.MPCPlannerNode", "MPCPlannerNode"),  # 导入整个模块（TBKNode 中的所有内容）
    ("utils.node_utils.GlobalPlannerNode", "GlobalPlannerNode"),  
]

# 动态导入模块，绑定到全局作用域
for module_path, class_name in modules_to_import:
    imported = try_import(module_path, class_name)
    if imported:
        if class_name:
            globals()[class_name] = imported  # 将类名绑定到全局作用域
        else:
            module_name = module_path.split('.')[-1]
            globals()[module_name] = imported  # 将模块名绑定到全局作用域