import dearpygui.dearpygui as dpg
from config.UiConfig import UiConfig
from utils.DataProcessor import ui_data


class UICallback:
    def __init__(self):
        pass

    def on_key_release(self, sender, app_data,user_data):
        config = user_data
        if dpg.is_key_down(dpg.mvKey_LControl) and app_data == dpg.mvKey_S:
            config.layout.save()
            print("布局保存成功")

    def on_mouse_move(self):
        ui_data.draw_mouse_pos_last = ui_data.draw_mouse_pos
        ui_data.draw_mouse_pos = dpg.get_drawing_mouse_pos()
        ui_data.mouse_move_pos = tuple(
            x - y for x, y in zip(ui_data.draw_mouse_pos, ui_data.draw_mouse_pos_last)
        )



class UI:
    def __init__(self, boxes):
        self.boxes = boxes
        self.config = UiConfig()
        self.is_created = False
        self._ui_callback = UICallback()

    def create(self):
        self.create_global_handler()
        dpg.create_viewport(title=self.config.title, width=1920, height=1080)
        dpg.configure_app(
            docking=True,
            docking_space=True,
            init_file=self.config.layout.init_file,
            load_init_file=True,
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        self.is_created = True

    def create_global_handler(self):
        with dpg.handler_registry() as global_hander:
            dpg.add_key_release_handler(callback=self._ui_callback.on_key_release, user_data=self.config)
            # dpg.add_mouse_move_handler(callback=self._ui_callback.on_mouse_move)
    def ui_loop(self):
        self._ui_callback.on_mouse_move()

    def run_loop(self, func=None):
        if func is not None:
            while dpg.is_dearpygui_running():
                self.ui_loop()
                func()
                dpg.render_dearpygui_frame()
        else:
            dpg.start_dearpygui()

    def show(self):
        if not self.is_created:
            self.create()
        for box in self.boxes:
            box.show()

    def update(self):
        for box in self.boxes:
            box.update()
