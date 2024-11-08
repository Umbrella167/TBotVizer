import re
import traceback
from contextlib import contextmanager
from typing import Generator, Union

from dearpygui import dearpygui as dpg

from utils.DataProcessor import UiData, TBKData


class DiyComponents:
    def __init__(self, data: UiData):
        self._data = data

    def set_input_color(self, change_item, color):
        with dpg.theme() as theme_id:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(
                    dpg.mvThemeCol_FrameBg, (0, 0, 0, 0), category=dpg.mvThemeCat_Core
                )
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
            print(
                f"ERROR(bind_item_theme)：\n    Item:{change_item}\n    File:{file_name}\n    Line:{line_number}\n    Function:{func_name}\n    Text:{text}"
            )

    def add_input(self, _type, tag, default_value, max_value, min_value, step):
        if _type == "int":
            # dpg.add_drag_int(clamped = True,tag=self._tag,default_value=value,width=-1,max_value=int(self.max),min_value=int(self.min),speed=int(self.step),callback=self.change_param_input_callback)
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

    class TableTree:
        def __init__(self):
            self.param_tag = ""
            pass

        def on_row_clicked(self, sender, value, user_data):
            # Make sure it happens quickly and without flickering
            with dpg.mutex():
                # We don't want to highlight the selectable as "selected"
                dpg.set_value(sender, False)

                table, row = user_data
                root_level, node = dpg.get_item_user_data(row)

                # First of all let's toggle the node's "expanded" status
                is_expanded = not dpg.get_value(node)
                dpg.set_value(node, is_expanded)
                # All children *beyond* this level (but not on this level) will be hidden
                hide_level = 10000 if is_expanded else root_level

                # Now manage the visibility of all the children as necessary
                rows = dpg.get_item_children(table, slot=1)
                root_idx = rows.index(row)
                # We don't want to look at rows preceding our current "root" node
                rows = rows[root_idx + 1:]
                for child_row in rows:

                    child_level, child_node = dpg.get_item_user_data(child_row)
                    if child_level <= root_level:
                        break

                    if child_level > hide_level:
                        dpg.hide_item(child_row)
                    else:
                        dpg.show_item(child_row)
                        hide_level = 10000 if dpg.get_value(
                            child_node) else child_level

        @contextmanager
        def table_tree_node(self, *cells: str, leaf: bool = False, tag=0) -> Generator[Union[int, str], None, None]:
            table = dpg.top_container_stack()
            cur_level = dpg.get_item_user_data(table) or 0

            node = dpg.generate_uuid()
            INDENT_STEP = 30
            with dpg.table_row(user_data=(cur_level, node)) as row:
                with dpg.group(horizontal=True, horizontal_spacing=0):
                    span_columns = True if cells[1] == "--" else False
                    dpg.add_selectable(span_columns=span_columns,
                                       callback=self.on_row_clicked, user_data=(table, row))
                    dpg.add_tree_node(
                        tag=node,
                        label=cells[0],
                        # indent=cur_level*INDENT_STEP,
                        selectable=False,
                        leaf=leaf,
                        default_open=True)

                for label in cells[1:]:
                    # print(label)
                    dpg.add_text(label, tag=tag)
            try:
                dpg.set_item_user_data(table, cur_level + 1)
                yield node
            finally:
                dpg.set_item_user_data(table, cur_level)

        def add_table_tree_leaf(self, *cells: str, tag=0) -> Union[int, str]:
            with self.table_tree_node(*cells, leaf=True, tag=tag) as node:
                pass
            return node

        def build_dpg_tree(self, tree):
            for key, value in tree.items():
                if isinstance(value, dict):
                    if 'info' in value and 'type' in value and 'value' in value:
                        print(value['info'], value['type'], value['value'])
                        self.add_table_tree_leaf(key, value['info'], value['type'], value['value'])
                    else:
                        with self.table_tree_node(key, "--", "--", "--"):
                            self.build_dpg_tree(value)
                            # self.param_tag = self.param_tag + "/" + value
                else:
                    print(key)

                    self.add_table_tree_leaf(key, "--", "--", str(value))

    class param_input:
        def __init__(self, outer_instance, data: UiData, tbkdata: TBKData) -> None:
            self._outer_instance = outer_instance
            self._tag = None
            self._value = None
            self._data = data
            self._tbkdata = tbkdata
            self._type = None
            self._info = None
            self._parent = None
            self.min = None
            self.max = None
            self.enum = []
            self.step = 1.0

        def get_limit(self):
            if self._info:
                self.enum = self._info
                pattern = r"\[(.*?)\]"
                match = re.search(pattern, self._info)
                if match:
                    content = match.group(1).split(",")
                    if len(content) == 3:
                        self.min = content[0]
                        self.max = content[1]
                        self.step = content[2]
                    elif len(content) == 2:
                        self.min = content[0]
                        self.max = content[1]
                    self.enum = content

        # 创建主题
        def create_theme(self):
            with dpg.theme() as theme_id:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(
                        dpg.mvThemeCol_FrameBg,
                        (0, 0, 0, 0),
                        category=dpg.mvThemeCat_Core,
                    )
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
            return theme_id

        def new_input(self, tag, value: str, type="str", info=None, parent=0):
            self._init_input(tag=tag, value=value, type=type, info=info, parent=parent)
            self.get_limit()
            theme_id = self.create_theme()
            # if self._type in self._uidata.intname:
            if any(item in self._type for item in self._data.intname):

                self.create_input_int()
            # elif self._type in self._uidata.floatname:
            elif any(item in self._type for item in self._data.floatname):

                self.create_input_float()
            # elif self._type in self._uidata.boolname:
            elif any(item in self._type for item in self._data.boolname):

                self.create_check_box()
            # elif self._type in self._uidata.enumname:
            elif any(item in self._type for item in self._data.enumname):
                self.create_enum()
            else:
                self.create_input_text()
            dpg.bind_item_theme(item=tag, theme=theme_id)

        def _init_input(self, tag, value: str, type="str", info=None, parent=0):
            self._value = value
            try:
                self._type = type.lower()
            except:
                self._type = type
            self._info = info
            self._parent = parent
            self._tag = tag

        def change_param_input_callback(self, sender, app_data):
            split_data = sender.split("_")[-1]
            end = split_data[0]
            head = sender[: -1 * (len(split_data) + 1)]
            param = f"{head}/__{end}__"
            value = "None" if app_data == "" else app_data
            if value == "None" or value == "":
                dpg.set_value(sender, value)
                self._outer_instance.set_input_color(sender, [255, 0, 0, 255])
            self._tbkdata.put_param(param, str(value))

        # 正整数输入框
        def create_input_int(self):
            try:
                value = int(self._value)
            except:
                value = 0
            if self.max and self.min:
                print(self.max, self.min)
                # self._outer_instance.add_input( "int",self._tag,50,100,0,10)
                # dpg.add_drag_int(
                #     clamped=True,
                #     tag=self._tag,
                #     default_value=value,
                #     width=-1,
                #     max_value=int(self.max),
                #     min_value=int(self.min),
                #     speed=int(self.step),
                #     callback=self.change_param_input_callback,
                # )
                dpg.add_slider_int(
                    clamped=True,
                    tag=self._tag,
                    default_value=value,
                    width=-1,
                    max_value=int(self.max),
                    min_value=int(self.min),
                    # speed=int(self.step),
                    callback=self.change_param_input_callback,
                )

            else:
                dpg.add_input_int(
                    tag=self._tag,
                    default_value=value,
                    width=-1,
                    callback=self.change_param_input_callback,
                )

        # 浮点数输入框

        def create_input_float(self):
            try:
                value = float(self._value)
            except:
                value = 0
            if self.max and self.min:
                dpg.add_drag_double(
                    clamped=True,
                    tag=self._tag,
                    default_value=value,
                    width=-1,
                    max_value=float(self.max),
                    min_value=float(self.min),
                    speed=float(self.step),
                    callback=self.change_param_input_callback,
                )
            else:
                dpg.add_input_double(tag=self._tag, default_value=value, width=-1)

        # 文本输入框

        def create_input_text(self):
            dpg.add_input_text(
                tag=self._tag,
                default_value=self._value,
                width=-1,
                callback=self.change_param_input_callback,
            )

        # 布尔输入框

        def create_check_box(self):
            def checkbos_callbak(sender, app_data):
                value = app_data
                split_data = sender.split("_")[-1]
                end = split_data[0]
                head = sender[: -1 * (len(split_data) + 1)]
                param = f"{head}/__{end}__"
                dpg.configure_item(sender, label=str(value))
                self._tbkdata.put_param(param, str(value))

            try:
                value = int(self._value)
                if value > 0:
                    value = True
                else:
                    value = False
            except:
                try:
                    value = self._value.lower()
                    value = True if value == "true" else False
                except:
                    value = False
            with dpg.group():
                dpg.add_checkbox(
                    tag=self._tag,
                    default_value=value,
                    label=str(value),
                    callback=checkbos_callbak,
                )

        # 枚举输入框

        def create_enum(self):
            enum = self.enum
            try:
                split_choose = self.enum.split("|")
                if len(split_choose) > 1:
                    enum = []
                    for item in split_choose:
                        enum.append(item)
                else:
                    enum = []
            except:
                pass
            if enum:
                dpg.add_combo(
                    tag=self._tag,
                    items=enum,
                    width=-1,
                    default_value=self._value,
                    callback=self.change_param_input_callback,
                )
            else:
                self.create_input_text()
