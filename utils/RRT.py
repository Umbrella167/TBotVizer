import python_motion_planning as pmp
import random
import time

def generate_random_circle_obstacles(num_obstacles, x_range, y_range, max_radius):
    obstacles = []
    for _ in range(num_obstacles):
        x = random.randint(0, x_range - 1)  # 随机生成圆心的x坐标
        y = random.randint(0, y_range - 1)  # 随机生成圆心的y坐标
        r = random.randint(1, max_radius)  # 随机生成半径（确保半径至少为1）
        obstacles.append([x, y, r])
    return obstacles

max_radius = 5
map = pmp.Map(9000, 9000)
map.obs_circ = generate_random_circle_obstacles(20000, 9000, 9000, max_radius)
print(map.obs_circ)
planner = pmp.RRTStar((5000, 5), (4005, 8000), map,max_dist=500)
cost, path, expand = planner.plan()