from ui.boxes import Box
import dearpygui.dearpygui as dpg

from utils.Utils import get_all_subclasses


class ConsoleBox(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.boxes = []
        self.all_classes =  get_all_subclasses(Box)
        self.generate_add_methods()

    def create(self):
        # 初始化设置
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="ConsoleBox")
        dpg.configure_item(
            self.tag,
            pos=[0, 0],
            height=1000,
            autosize=True,
            menubar=True,
            collapsed=False,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_close=True,
            no_saved_settings=True,
            no_title_bar=True,
        )

    def generate_add_methods(self):
        for cls in self.all_classes:
            if cls == self.__class__:
                continue
            method_name = f"add_{cls.__name__}"
            # 使用闭包捕获cls
            def add_method(self, cls=cls, **kwargs):
                try:
                    instance = cls(**kwargs)
                    self.boxes.append(instance)
                    print(f"{cls.__name__} 实例已添加到 boxes 列表中。")
                except TypeError as e:
                    print(f"无法实例化 {cls.__name__}：{e}")
            # 将生成的方法绑定到当前实例
            setattr(self, method_name, add_method.__get__(self))


        # for subclass in get_all_subclasses(Box):
        #     if subclass == self.__class__:
        #         continue
        #     instance = subclass()
        #     self.boxes.append(instance)
        # print(self.boxes)
