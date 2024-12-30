# import dearpygui.dearpygui as dpg
# import re
#
# from static.Params import TypeParams
# from utils.DataProcessor import TBKData
# from utils.Utils import set_input_color
#
# """
# 有用到但是没做测试，需要进一步测试看看
# """
#
# class Input:
#     # def __init__(self, outer_instance, tbk_data: TypeParams, tbk_data: TBKData) -> None:
#     def __init__(self, data: TypeParams, tbkdata: TBKData) -> None:
#
#         # self._outer_instance = outer_instance
#         self._tag = None
#         self._value = None
#         self._data = data
#         self._tbkdata = tbkdata
#         self._type = None
#         self._info = None
#         self._parent = None
#         self.min = None
#         self.max = None
#         self.enum = []
#         self.step = 1.0
#
#     def get_limit(self):
#         if self._info:
#             self.enum = self._info
#             pattern = r"\[(.*?)\]"
#             match = re.search(pattern, self._info)
#             if match:
#                 content = match.group(1).split(",")
#                 if len(content) == 3:
#                     self.min = content[0]
#                     self.max = content[1]
#                     self.step = content[2]
#                 elif len(content) == 2:
#                     self.min = content[0]
#                     self.max = content[1]
#                 self.enum = content
#
#     # 创建主题
#     def create_theme(self):
#         with dpg.theme() as theme_id:
#             with dpg.theme_component(dpg.mvAll):
#                 dpg.add_theme_color(
#                     dpg.mvThemeCol_FrameBg,
#                     (0, 0, 0, 0),
#                     category=dpg.mvThemeCat_Core,
#                 )
#                 dpg.add_theme_color(
#                     dpg.mvThemeCol_FrameBgHovered,
#                     (0, 0, 0, 0),
#                     category=dpg.mvThemeCat_Core,
#                 )
#                 dpg.add_theme_color(
#                     dpg.mvThemeCol_FrameBgActive,
#                     (0, 0, 0, 0),
#                     category=dpg.mvThemeCat_Core,
#                 )
#         return theme_id
#
#     def new_input(self, tag, value: str, type="str", info=None, parent=0):
#         self._init_input(tag=tag, value=value, type=type, info=info, parent=parent)
#         self.get_limit()
#         theme_id = self.create_theme()
#         # if self._type in self._type_params.intname:
#         if self._type.lower() == "int":
#             self.create_input_int()
#         # elif self._type in self._type_params.floatname:
#         elif self._type.lower() == 'float':
#             self.create_input_float()
#         # elif self._type in self._type_params.boolname:
#         elif self._type.lower() == 'bool':
#
#             self.create_check_box()
#         # elif self._type in self._type_params.enumname:
#         elif self._type.lower() == 'enum':
#             self.create_enum()
#         else:
#             self.create_input_text()
#         dpg.bind_item_theme(item=tag, theme=theme_id)
#
#     def _init_input(self, tag, value: str, type="str", info=None, parent=0):
#         self._value = value
#         try:
#             self._type = type.lower()
#         except:
#             self._type = type
#         self._info = info
#         self._parent = parent
#         self._tag = tag
#
#     def change_param_input_callback(self, sender, app_data):
#         split_data = sender.split("_")[-1]
#         end = split_data[0]
#         head = sender[: -1 * (len(split_data) + 1)]
#         param = f"{head}/__{end}__"
#         value = "None" if app_data == "" else app_data
#         if value == "None" or value == "":
#             dpg.set_value(sender, value)
#             set_input_color(sender, [255, 0, 0, 255])
#         self._tbkdata.put_param(param, str(value))
#
#     # 正整数输入框
#     def create_input_int(self):
#         try:
#             value = int(self._value)
#         except:
#             value = 0
#         if self.max and self.min:
#             dpg.add_slider_int(
#                 clamped=True,
#                 tag=self._tag,
#                 default_value=value,
#                 width=-1,
#                 max_value=int(self.max),
#                 min_value=int(self.min),
#                 # speed=int(self.step),
#                 callback=self.change_param_input_callback,
#             )
#
#         else:
#             dpg.add_input_int(
#                 tag=self._tag,
#                 default_value=value,
#                 width=-1,
#                 callback=self.change_param_input_callback,
#             )
#
#     # 浮点数输入框
#
#     def create_input_float(self):
#         try:
#             value = float(self._value)
#         except:
#             value = 0
#         if self.max and self.min:
#             dpg.add_drag_double(
#                 clamped=True,
#                 tag=self._tag,
#                 default_value=value,
#                 width=-1,
#                 max_value=float(self.max),
#                 min_value=float(self.min),
#                 speed=float(self.step),
#                 callback=self.change_param_input_callback,
#             )
#         else:
#             dpg.add_input_double(tag=self._tag, default_value=value, width=-1)
#
#     # 文本输入框
#
#     def create_input_text(self):
#         dpg.add_input_text(
#             tag=self._tag,
#             default_value=self._value,
#             width=-1,
#             callback=self.change_param_input_callback,
#         )
#
#     # 布尔输入框
#
#     def create_check_box(self):
#         def checkbos_callbak(sender, app_data):
#             value = app_data
#             split_data = sender.split("_")[-1]
#             end = split_data[0]
#             head = sender[: -1 * (len(split_data) + 1)]
#             param = f"{head}/__{end}__"
#             dpg.configure_item(sender, label=str(value))
#             self._tbkdata.put_param(param, str(value))
#
#         try:
#             value = int(self._value)
#             if value > 0:
#                 value = True
#             else:
#                 value = False
#         except:
#             try:
#                 value = self._value.lower()
#                 value = True if value == "true" else False
#             except:
#                 value = False
#         with dpg.group():
#             dpg.add_checkbox(
#                 tag=self._tag,
#                 default_value=value,
#                 label=str(value),
#                 callback=checkbos_callbak,
#             )
#
#     # 枚举输入框
#
#     def create_enum(self):
#         enum = self.enum
#         try:
#             split_choose = self.enum.split("|")
#             if len(split_choose) > 1:
#                 enum = []
#                 for item in split_choose:
#                     enum.append(item)
#             else:
#                 enum = []
#         except:
#             pass
#         if enum:
#             dpg.add_combo(
#                 tag=self._tag,
#                 items=enum,
#                 width=-1,
#                 default_value=self._value,
#                 callback=self.change_param_input_callback,
#             )
#         else:
#             self.create_input_text()
