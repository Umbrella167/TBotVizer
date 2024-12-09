import math
import pickle
import traceback

import dearpygui.dearpygui as dpg
import numpy as np

from static.Params import TypeParams
from utils.ClientLogManager import client_logger


def new_texture(image):
    height, width, _ = image.shape
    texture_data = image.ravel().astype("float32") / 255
    with dpg.texture_registry():
        texture_tag = dpg.add_raw_texture(width=width, height=height, default_value=texture_data,
                                          format=dpg.mvFormat_Float_rgba)
    return texture_tag

def convert_to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0

def set_itme_text_color(item, color):
    with dpg.theme() as input_text:
        with dpg.theme_component(dpg.mvInputText):
            dpg.add_theme_color(dpg.mvThemeCol_Text, color)
        dpg.bind_item_theme(item, input_text)


def item_auto_resize(item, parent, height_rate: float = 0, width_rate: float = 0, min_width=None, max_width=None):
    def resize_callback(sender, app_data, user_data):
        parent_width, parent_height = dpg.get_item_rect_size(parent)
        new_width = parent_width * width_rate if width_rate > 0 else None
        new_height = parent_height * height_rate if height_rate > 0 else None
        if new_width is not None:
            if min_width is not None and new_width < min_width:
                new_width = min_width
            elif max_width is not None and new_width > max_width:
                new_width = max_width
            dpg.configure_item(item, width=new_width)
        if new_height is not None:
            dpg.configure_item(item, height=new_height)

    with dpg.item_handler_registry() as handler:
        dpg.add_item_resize_handler(callback=resize_callback)
    dpg.bind_item_handler_registry(parent, handler)


def get_mouse_relative_pos(parent):
    pos = dpg.get_mouse_pos(local=False)
    children = dpg.get_item_children(parent, slot=1)
    ref_node = children[0]
    ref_screen_pos = dpg.get_item_rect_min(ref_node)
    NODE_PADDING = (18, 18)
    pos[0] = pos[0] - (ref_screen_pos[0] - NODE_PADDING[0])
    pos[1] = pos[1] - (ref_screen_pos[1] - NODE_PADDING[1])
    return pos


def calculate_distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def middle_pos(pos1, pos2):
    return [(pos1[0] + pos2[0]) / 2, (pos1[1] + pos2[1]) / 2]


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
def mouse2ssl(x, y, translation_matrix, scale):
    x1, y1 = (matrix2list_mouse(translation_matrix) @ np.array([x, y, 1, 1]))[:2]
    return int(x1 / scale), int(-1 * y1 / scale)


def swap_elements(lst, element1, element2):
    try:
        # 找到元素的索引
        index1 = lst.index(element1)
        index2 = lst.index(element2)
        # 交换元素
        lst[index1], lst[index2] = lst[index2], lst[index1]
    except ValueError:
        client_logger.log("ERROR", "Utils/swap_elements: One of the elements is not in the list!")


def check_is_created(func):
    def wrapper(self, *args, **kwargs):
        if self.is_created:
            client_logger.log("DEBUG", f"{self.__class__.__name__} is already created.")
            return
        return func(self, *args, **kwargs)

    return wrapper


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
                if nested_changes["added"] or nested_changes["removed"] or nested_changes["modified"]:
                    modified[key] = nested_changes
            elif dict1[key] != dict2[key]:
                # 如果值不相等，记录修改
                modified[key] = (dict1[key], dict2[key])

    for key in dict2.keys():
        if key not in dict1:
            added[key] = dict2[key]

    return {"added": added, "removed": removed, "modified": modified}


def build_message_tree(data):
    tree = {}
    for uuid in data:
        puuid = f"{data[uuid].ep_info.node_name}_{data[uuid].puuid}"
        if puuid not in tree:
            tree[puuid] = {}
        tree[puuid][uuid] = data[uuid]
    return tree


def build_param_tree(flat_dict):
    tree = {}

    for key, value in flat_dict.items():
        parts = key.split("/")
        current_level = tree

        for part in parts[:-1]:  # 遍历层级中的所有部分（除了最后一个）
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

        # 处理最后一个部分，可能包含冒号
        last_part = parts[-1]
        sub_parts = last_part.split(":")

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


def set_input_color(change_item, color):
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0, 0, 0, 0), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(
                dpg.mvThemeCol_FrameBgHovered,
                (0, 0, 0, 0),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_FrameBgActive,
                (0, 0, 0, 0),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_color(dpg.mvThemeCol_Text, color)

    try:
        dpg.bind_item_theme(item=change_item, theme=theme_id)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        file_name, line_number, func_name, text = tb[-1]
        client_logger.log(
            "ERROR",
            f"ERROR(bind_item_theme)：\n    Item:{change_item}\n    File:{file_name}\n    Line:{line_number}\n    Function:{func_name}\n    Text:{text}",
        )


# 这个不知道是啥也没用到
def add_input(_type, tag, default_value, max_value, min_value, step):
    if _type == "int":
        # dpg.add_drag_int(clamped = True,tag=self._tag,default_value=value,_width=-1,max_value=int(self.max),min_value=int(self.min),speed=int(self.step),callback=self.change_param_input_callback)
        with dpg.group():
            dpg.add_drag_int(
                tag=tag,
                clamped=True,
                width=-1,
                default_value=int(default_value),
                max_value=int(max_value),
                min_value=int(min_value),
                speed=int(step),
            )
            dpg.add_slider_int(height=10, width=-1)


# 反序列化msg数据
def msg_serializer(msg, msg_type):
    if msg_type in TypeParams.PYTHON_TYPES:
        real_msg = pickle.loads(msg)
    else:
        real_msg = TypeParams.TBK_TYPES[msg_type]
        real_msg.ParseFromString(msg)
    return real_msg


# 获取所有子类
def get_all_subclasses(cls):
    subclasses = cls.__subclasses__()
    all_subclasses = []
    for subclass in subclasses:
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))
    return all_subclasses


def clear_nested_dictionaries(dict_obj):
    """Recursively clear all nested dictionaries."""
    print(dict_obj)
    for key in list(dict_obj.keys()):
        if isinstance(dict_obj[key], dict):
            # If the value is a dictionary, clear it
            clear_nested_dictionaries(dict_obj[key])
            dict_obj[key] = {}
        else:
            # If the value is not a dictionary, just remove the key
            del dict_obj[key]
