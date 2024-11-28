from utils.Utils import convert_to_float
from utils.node_utils.BaseFunc import BaseFunc


class Map(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {
            "vx": None,  # 输入值 vx
            "vy": None,  # 输入值 vy
            "alphax": None,  # 输入值 alphax
            "original_upper": 1,
            "original_lower": -1,
            "upper": 5000,  # 映射区间上限
            "lower": -5000  # 映射区间下限
        }
        self.output_data = {
            "mapped_value": None  # 映射后的值
        }

    def calc(self):
        super().calc()
        # 获取输入值并转换为浮点数
        vx = convert_to_float(self.input_data["vx"])
        vy = convert_to_float(self.input_data["vy"])
        alphax = convert_to_float(self.input_data["alphax"])
        original_upper = convert_to_float(self.input_data["original_upper"])
        original_lower = convert_to_float(self.input_data["original_lower"])
        upper = convert_to_float(self.input_data["upper"])
        lower = convert_to_float(self.input_data["lower"])

        # 检查输入区间是否有效。如果无效，直接退出，输出保持为 None
        if original_upper <= original_lower or upper < lower:
            self.output_data["mapped_value"] = None
            return

        # 定义映射方法
        def map_value(value):
            if value is None:
                return None
            # 将值归一化到 [0, 1] 的范围
            normalized_value = (value - original_lower) / (original_upper - original_lower)
            if normalized_value < 0:
                normalized_value = 0
            elif normalized_value > 1:
                normalized_value = 1
            # 将归一化后的值映射到目标区间 [lower, upper]
            return lower + normalized_value * (upper - lower)

        # 对 vx, vy, 和 alphax 分别进行映射
        self.output_data["mapped_value"] = [map_value(vx), map_value(vy), map_value(alphax)]
