from dataclasses import dataclass
@dataclass(frozen=True)
class AGVParam:
    # 一个step内最多的点数
    MAX_POINTS = 60000

    # 每隔PATH_STEP保存一次点云
    PATH_STEP = 2000

    # 点云的单位 * LOCAL_SCALE
    LOCAL_SCALE = 1000

    # 点云大小
    GFX_POINTS_SIZE = 3
    # 保留高度在RANGE内的点
    HIGH_RANGE_GLOBAL = [-1e9, 1e9]
    
    # HIGH_RANGE_GLOBAL = [-10, 1000]
    
    HIGH_RANGE_MAP = [10, 1000]

    # 画布大小
    CANVAS_SIZE = (1920, 1080)

    # 距离阈值(保留 DISTANCE_THRESHOLD% 的点)
    DISTANCE_THRESHOLD = 75

    GRID_SIZE = (-10000, 10000)
    RESOLUTION = 500

    RARE_DATA = {
        # 稀疏高度大于HIGHT_THRESHOLD
        "HIGHT_THRESHOLD": 1000 ,
        # 抽样率
        "SAMPLE_RATE": 0.4,
    }