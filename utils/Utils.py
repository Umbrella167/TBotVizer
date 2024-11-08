import dearpygui.dearpygui as dpg
import math
import numpy as np

def calculate_distance( pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
def middle_pos( pos1, pos2):
    return [(pos1[0] + pos2[0]) / 2,(pos1[1] + pos2[1]) / 2]
def calculate_center_point(points):
    """
    计算四边形的中心点
    :param points: 四边形四个点的坐标列表 [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
    :return: 四边形中心点的坐标 (x, y)
    """
    x_coords = [point[0] for point in points]
    y_coords = [point[1] for point in points]
    
    center_x = sum(x_coords) / 4
    center_y = sum(y_coords) / 4
    
    return center_x, center_y

def apply_transform(matrix, point):
    # 将 DearPyGui 矩阵转换为 NumPy 矩阵
    np_matrix = np.array(matrix).reshape(3, 3)
    # 确保 point 是 [x, y, 1]
    point = np.array([point[0], point[1], 1])
    # 进行矩阵乘法
    transformed_point = np_matrix @ point
    return transformed_point[:2]  # 返回 [x, y]

def matrix2list_mouse(matrix):
    transform = []
    for i in range(16):
        transform.append(matrix[i])
    data_array = np.array(transform)
    matrix = data_array.reshape(4, 4)
    matrix[0, 3] = -1 * matrix[-1, 0]
    matrix[1, 3] = -1 * matrix[-1, 1]
    matrix[-1, 0] = 0
    matrix[-1, 1] = 0
    return np.array(matrix)
def matrix2list(matrix):
    transform = []
    for i in range(16):
        transform.append(matrix[i])
    data_array = np.array(transform)
    matrix = data_array.reshape(4, 4)
    matrix[0, 3] = matrix[-1, 0]
    matrix[1, 3] = matrix[-1, 1]
    matrix[-1, 0] = 0
    matrix[-1, 1] = 0
    return np.array(matrix)
# def get_texture_data(image):
#     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     image = cv2.flip(image,2)
#     texture_data = image.ravel().astype('float32') / 255
#     return texture_data
def mouse2ssl(x,y,translation_matrix,scale):
    x1,y1 = (matrix2list_mouse(translation_matrix) @ np.array([x,y,1,1]))[:2]
    return int(x1 / scale),int(-1 * y1 / scale)

def swap_elements(lst, element1, element2):
    try:
        # 找到元素的索引
        index1 = lst.index(element1)
        index2 = lst.index(element2)
        # 交换元素
        lst[index1], lst[index2] = lst[index2], lst[index1]
    except ValueError:
        print("其中一个元素不在列表中")
# def compare_dicts(dict1, dict2):
#     keys1 = set(dict1.keys())
#     keys2 = set(dict2.keys())

#     added_keys = keys2 - keys1
#     removed_keys = keys1 - keys2
#     common_keys = keys1 & keys2
#     modified_items = {key: dict2[key] for key in common_keys if dict1[key] != dict2[key]}
#     return added_keys, removed_keys, modified_items
# def compare_dicts(dict1, dict2):  
#     added = {k: dict2[k] for k in dict2 if k not in dict1}  
#     removed = {k: dict1[k] for k in dict1 if k not in dict2}  
#     modified = {k: (dict1[k], dict2[k]) for k in dict1 if k in dict2 and dict1[k] != dict2[k]}  

#     return {  
#         'added': added,  
#         'removed': removed,  
#         'modified': modified  
#     }


def compare_dicts(dict1, dict2):  
    added = {}  
    removed = {}  
    modified = {}  

    # 处理新增和删除的键  
    for key in dict1.keys():  
        if key not in dict2:  
            removed[key] = dict1[key]  
        else:  
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):  
                # 如果值是字典，递归比较  
                nested_changes = compare_dicts(dict1[key], dict2[key])  
                if nested_changes['added'] or nested_changes['removed'] or nested_changes['modified']:  
                    modified[key] = nested_changes  
            elif dict1[key] != dict2[key]:  
                # 如果值不相等，记录修改  
                modified[key] = (dict1[key], dict2[key])  

    for key in dict2.keys():  
        if key not in dict1:  
            added[key] = dict2[key]  

    return {  
        'added': added,  
        'removed': removed,  
        'modified': modified  
    }  

def build_message_tree(data):
    tree = {}
    
    for item in data.values():
        puuid = item.puuid
        node_name = item.node_name
        name = item.name
        msg_name = item.msg_name

        if puuid not in tree:
            tree[puuid] = {}
        if node_name not in tree[puuid]:
            tree[puuid] = {node_name: {}}
        if name not in tree[puuid][node_name]:
            tree[puuid][node_name][name] = []
        
        tree[puuid][node_name][name].append(msg_name)
    
    return tree

def build_param_tree(flat_dict):
    tree = {}
    
    for key, value in flat_dict.items():
        parts = key.split('/')
        current_level = tree
        
        for part in parts[:-1]:  # 遍历层级中的所有部分（除了最后一个）
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        
        # 处理最后一个部分，可能包含冒号
        last_part = parts[-1]
        sub_parts = last_part.split(':')
        
        for sub_part in sub_parts[:-1]:
            if sub_part not in current_level:
                current_level[sub_part] = {}
            current_level = current_level[sub_part]
        
        # 最后的部分是叶节点
        current_level[sub_parts[-1]] = value
    
    return tree

def get_tree_depth(tree, current_depth=0):
    if not isinstance(tree, dict) or not tree:
        # 如果不是字典或者字典为空，返回当前深度
        return current_depth
    # 递归遍历子树，并计算每个子树的深度
    return max(get_tree_depth(value, current_depth + 1) for value in tree.values())