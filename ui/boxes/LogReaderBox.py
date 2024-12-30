import dearpygui.dearpygui as dpg

from api.NewTBKApi import tbk_manager

from logger.logger import Logger
from ui.boxes.BaseBox import BaseBox
from utils.ClientLogManager import client_logger
from utils.Utils import set_itme_text_color


class LogReaderBox(BaseBox):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._logger = Logger()
        self._callback = LogReaderCallback(self._logger)
        self._canvas = None
        self.texture_tag = {}
        self.slider_tag = None
        self.is_play = False
        self.start_button_tag = None

    def create(self):
        dpg.configure_item(self.tag, label="LogReaderBox", height=250, width=500)
        with dpg.texture_registry():
            image_button_name = ["start", "stop", "next", "last"]
            for name in image_button_name:
                width, height, _, data = dpg.load_image(f"static/image/{name}.png")
                self.texture_tag[name] = dpg.add_static_texture(width=width, height=height, default_value=data)
        with dpg.group(parent=self.tag):
            self.path_input_tag = dpg.add_input_text(hint="Log Path", width=-1)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Open File", callback=lambda: dpg.show_item(self.file_dialog_tag))
                dpg.add_button(
                    label="Import",
                    callback=self._callback.import_log,
                    user_data=(self.path_input_tag, self.get_slider_tag),
                )
        with dpg.child_window(parent=self.tag, width=-1) as self.logreader_child_window_tag:
            dpg.add_text("Log Reader:")
            with dpg.group(horizontal=True):
                dpg.add_image_button(
                    self.texture_tag["last"],
                    uv_max=[1, 1],
                    uv_min=[0, 0],
                    width=30,
                    height=30,
                    callback=self._callback.last_message,
                )
                dpg.add_image_button(
                    self.texture_tag["start"],
                    uv_max=[1, 1],
                    uv_min=[0, 0],
                    width=30,
                    height=30,
                    callback=self._callback.play_message,
                    user_data=(self.texture_tag, dpg.last_item() + 1, self.get_slider_tag),
                )
                dpg.add_image_button(
                    self.texture_tag["next"],
                    uv_max=[1, 1],
                    uv_min=[0, 0],
                    width=30,
                    height=30,
                    callback=self.next_msg,
                )
            self.slider_tag = dpg.add_slider_double(
                width=-1,
                label="Slider",
                max_value=0,
                callback=self._callback.read_log_by_timestamp,
                user_data=self.get_slider_tag,
            )
        with dpg.handler_registry():
            dpg.add_key_press_handler(key=dpg.mvKey_Left, callback=self.prev_msg)
            dpg.add_key_press_handler(key=dpg.mvKey_Right, callback=self.next_msg)
        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                width=700,
                height=400,
                default_path="logs/msg_log",
                callback=lambda sender, app_data: dpg.set_value(self.path_input_tag, app_data["file_path_name"]),
        ) as self.file_dialog_tag:
            dpg.add_file_extension(
                "Source files (*.tzlog){.tzlog}",
                color=(0, 255, 255, 255),
            )
            dpg.add_file_extension(".*")

    def prev_msg(self):
        prev_msg = self._callback.log.get_prev_msg()
        if prev_msg is None:
            return
        puuid = prev_msg["puuid"]
        msg_name = prev_msg["msg_name"]
        name = prev_msg["name"]
        self._callback.log_publish_dict[puuid][msg_name][name].publish(prev_msg["message"])
        current_time = (prev_msg["timestamp"] - self._callback.log_start_time) / 1e9
        dpg.set_value(self.slider_tag, current_time)

    def get_slider_tag(self):
        return self.slider_tag

    def next_msg(self):
        next_msg = self._callback.log.get_next_msg()
        if next_msg is None:
            return
        puuid = next_msg["puuid"]
        msg_name = next_msg["msg_name"]
        name = next_msg["name"]
        self._callback.log_publish_dict[puuid][msg_name][name].publish(next_msg["message"])
        current_time = (next_msg["timestamp"] - self._callback.log_start_time) / 1e9
        dpg.set_value(self.slider_tag, current_time)

    def update(self):
        slider_timestamp = self._callback.log_start_time + dpg.get_value(self.slider_tag) * 1e9
        if self._callback.is_play and self._callback.is_log_open:
            self.next_msg()


class LogReaderCallback:
    def __init__(self, logger: Logger):
        self._logger = logger
        self.log = None
        self.log_publish_dict = {}
        self.is_play = False
        self.is_log_open = False
        self.log_start_time = 0

    def read_log_by_timestamp(self, sender, app_data, user_data):
        slider_tag = user_data
        slider_tag = slider_tag()
        if self.log is None:
            return
        slider_timestamp = self.log_start_time + dpg.get_value(slider_tag) * 1e9
        now_msg = self.log.read_log_by_timestamp(slider_timestamp)

    def import_log(self, sender, app_data, user_data):
        path_input_tag, slider_tag = user_data
        slider_tag = slider_tag()
        path = dpg.get_value(path_input_tag)
        log = self._logger.open(path)
        if not log.is_open:
            client_logger.log("error", "Failed to open log file.")
            self.is_log_open = False
            set_itme_text_color(path_input_tag, (255, 0, 0, 255))
            return
        self.log = log
        self.log_start_time = self.log.get_start_time
        self.is_log_open = True
        client_logger.log("success", f"Opening log file: {path}")
        set_itme_text_color(path_input_tag, (0, 255, 0, 255))
        log_time = log.get_total_time()
        dpg.configure_item(slider_tag, max_value=log_time)
        now_msg = self.log.read_log_by_timestamp(0)
        self.publish_log()

    def publish_log(self):
        if self.log is None:
            return
        logs = self.log.get_log_info()
        for (puuid, msg_name, name, msg_type), count in logs.items():
            # node_name = puuid.split("_")[:-1][0]
            # puuid_real = puuid.split("_")[-1]
            self.log_publish_dict.setdefault(puuid, {}).setdefault(msg_name, {}).setdefault(name, {})
            self.log_publish_dict[puuid][msg_name][name] = tbk_manager.publisher(
                info={
                    "name": name,
                    "msg_name": f"LOG_{msg_name}",
                    "msg_type": msg_type,
                }
            )

    def last_message(self):
        if self.log is None:
            return

    def play_message(self, sender, app_data, user_data):
        texture_tag, start_button_tag, slider_tag = user_data
        slider_tag = slider_tag()
        self.is_play = not self.is_play
        if self.is_play and self.is_log_open:
            dpg.configure_item(start_button_tag, texture_tag=texture_tag["stop"])
        elif not self.is_play and self.is_log_open:
            dpg.configure_item(start_button_tag, texture_tag=texture_tag["start"])
        else:
            client_logger.log("warning", "Please import log file!")

    def next_message(self):
        if self.log is None:
            return
