import json

import dearpygui.dearpygui as dpg

from config.SystemConfig import config
from static.Params import language


class LayoutManager:
    def __init__(self, theme="Dark", font_size=20, init_file="static/layout/ui_layout.ini",
                 settings_file="layout_settings.json"):
        # 初始化布局管理器，设置保存布局的文件名
        self.settings_file = settings_file
        self.init_file = init_file
        self.theme = theme
        self.font_size = font_size
        self.set_theme(self.theme)
        self.set_font(self.font_size)

    def save(self):
        dpg.save_init_file(self.init_file)
        """
        # 保存当前布局设置到文件
        layout_data = {}

        将当前布局保存到临时文件"ui_layout.ini"

        # 遍历所有项目，获取其别名和类型
        for item in dpg.get_all_items():
            item = dpg.get_item_alias(item)
            if item:
                _type = item.split("_")[-1]
                # 如果项目是复选框类型，保存其当前值
                if _type == "checkbox":
                    layout_data[item] = {
                        "value": dpg.get_value(item),
                    }
                if _type == "window":
                    layout_data[item] = {
                        "size": dpg.get_item_rect_size(item),
                    }
                if _type == "radiobutton":
                    layout_data[item] = {
                        "value": dpg.get_value(item),
                    }
                if _type == "treenode":
                    layout_data[item] = {
                        "value": dpg.get_value(item),
                    }
        # 获取视口的当前高度和宽度
        viewport_height = dpg.get_viewport_height()
        viewport_width = dpg.get_viewport_width()
        layout_data["viewport"] = {
            "_height": viewport_height,
            "_width": viewport_width,
        }
        # 将布局数据保存到JSON文件中
        with open(self.settings_file, "w") as file:
            json.dump(layout_data, file)
        """

    def load(self):
        # 从文件中加载布局设置
        # 这句在uimporti.show()里已经被用到了,这里暂时保留两个，但是没啥用
        dpg.configure_app(init_file=self.init_file)
        """
        try:
            with open(self.settings_file, "r") as file:
                layout_data = json.load(file)

            for item, properties in layout_data.items():
                if not dpg.does_item_exist(item):
                    continue
                # 设置视口的高度和宽度
                if item == "viewport":
                    dpg.set_viewport_height(properties["_height"])
                    dpg.set_viewport_width(properties["_width"])
                # 如果项目存在，设置其值
                if dpg.does_item_exist(item):
                    # 如果项目是复选框类型，设置之前保存的值
                    type = item.split("_")[-1]
                    if type == "checkbox":
                        dpg.set_value(item, properties["value"])
                    if type == "radiobutton":
                        dpg.set_value(item, properties["value"])
                    if type == "treenode":
                        dpg.set_value(item, properties["value"])
                    # 如果项目有回调函数，尝试执行回调函数
                    func = dpg.get_item_callback(item)
                    if func:
                        try:
                            func()
                        except Exception as e:
                            prin(f"Error while executing callback for {item}: {e}")
            prin("LayoutManager loaded")
        except FileNotFoundError:
            prin("No layout_manager settings found")
        """

    def get_drawer_window_size(self):
        try:
            with open(self.settings_file, "r") as file:
                layout_data = json.load(file)
            for item, properties in layout_data.items():
                if item == "drawer_window":
                    return properties["size"]
        except:
            pass
        return [0, 0]

    # 主题
    def set_theme(self, theme):
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                if theme == "Dark":
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (36, 36, 36, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (60, 60, 60, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (80, 80, 80, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (80, 80, 80, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 100, 100, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (120, 120, 120, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (50, 50, 50, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (70, 70, 70, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (90, 90, 90, 255))
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                    dpg.add_theme_color(dpg.mvThemeCol_Header, (70, 70, 70, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (90, 90, 90, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (110, 110, 110, 255))
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 5)

                if theme == "Light":
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (240, 240, 240, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (220, 220, 220, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (200, 200, 200, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 200, 200, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (180, 180, 180, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (160, 160, 160, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 0, 0, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (230, 230, 230, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (210, 210, 210, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (190, 190, 190, 255))
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                    dpg.add_theme_color(dpg.mvThemeCol_Header, (70, 70, 70, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (90, 90, 90, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (110, 110, 110, 255))
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 5)
        dpg.bind_theme(global_theme)

    def set_font(self, size=25):
        # 创建字体注册器
        with dpg.font_registry():
            # 加载字体，并设置字体大小为15
            with dpg.font(
                    config.FONT_FILE, size, pixel_snapH=True
            ) as chinese_font:
                # 添加字体范围提示，指定字体应包含完整的中文字符集
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
                # 以下是其他语言的字符集
                #    Options:
                #        mvFontRangeHint_Japanese
                #        mvFontRangeHint_Korean
                #        mvFontRangeHint_Chinese_Full
                #        mvFontRangeHint_Chinese_Simplified_Common
                #        mvFontRangeHint_Cyrillic
                #        mvFontRangeHint_Thai
                #        mvFontRangeHint_Vietnamese
        dpg.bind_font(chinese_font)

    # 语言
    def choose_lanuage(self, country):
        current_language = country
        label = language[current_language]
        dpg.set_item_label("main_window", label["main_window"])
        dpg.set_item_label("view_menu", label["view_menu"])
        dpg.set_item_label("theme_menu", label["theme_menu"])
        dpg.set_item_label("dark_theme", label["dark_theme"])
        dpg.set_item_label("light_theme", label["light_theme"])
        dpg.set_item_label("language_label", label["language_label"])
        dpg.set_item_label("chineseS_menu", label["chineseS_menu"])
        dpg.set_item_label("english_menu", label["english_menu"])
        dpg.set_item_label("english_menu", label["english_menu"])
