import dearpygui.dearpygui as dpg
from collections import deque
import tbkpy._core as tbkpy
import time
from static.Params import TypeParams
from google.protobuf.json_format import MessageToDict
from loguru import logger as uilogger
import pickle
from ui.boxes import Box

class PlotUitls:
    @staticmethod
    def is_plot_supported(tbk_type):
        if tbk_type not in TypeParams.PLOT_SUPPORT_TYPES:
            return False
        return True

    @staticmethod
    def tbkdata2plotdata(data, data_type):
        if not PlotUitls.is_plot_supported(data_type):
            uilogger.error("Unsupported data type")
            return
        if data_type in TypeParams.PYTHON_TYPES:
            if data_type == 'int' or data_type == 'float':
                res = {'0': data}
            elif data_type == 'list' or data_type == 'tuple':
                res = {}
                for i in range(len(data)):
                    res[str(i)] = data[i]
            else:
                res = data
                # print(res)
        else:
            res = MessageToDict(data, preserving_proto_field_name=True)
        return res


class TimedDeque:
    def __init__(self, max_age_seconds):
        self.items_with_timestamps = []  # List to store (item, timestamp) tuples
        self.items = []  # List to store only items for direct access
        self.max_age_seconds = max_age_seconds

    def append(self, item):
        # Add item along with the current timestamp
        current_time = time.time()
        self.items_with_timestamps.append((item, current_time))
        self.items.append(item)
        self._remove_old_items()

    def _remove_old_items(self):
        # Remove items that have exceeded the time limit
        current_time = time.time()
        while self.items_with_timestamps and (current_time - self.items_with_timestamps[0][1]) > self.max_age_seconds:
            self.items_with_timestamps.pop(0)
            self.items.pop(0)

    def __iter__(self):
        # Directly iterate over the items list
        return iter(self.items)

    def __len__(self):
        # Return the number of items
        return len(self.items)

    def get_items(self):
        # Directly return the list of items
        return self.items


class PlotVzBox(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plot_x_tag = None
        self.plot_y_tag = None
        self.plot_tag = None
        self.subscriber_func = {}
        self.subscription_data = {}
        self.is_axis_move = True
        self.data_start_time = time.time()
        self.now_time = time.time()
        self.max_save_time = 5  # 数据保存的最大时间限制

    def toggle_axis_move(self, sender, app_data,user_data):
        box_tag = user_data
        if not dpg.is_item_focused(box_tag):
            return 
        self.is_axis_move = not self.is_axis_move

    def show(self):
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="Plot Visualizer")
        # 添加标题
        dpg.add_text("Plot Visualizer", parent=self.tag)
        # 添加画轴
        self.plot_tag = dpg.add_plot(
            width=-1,
            height=-1,
            label="Plot Tools",
            payload_type="plot_data",
            drop_callback=self.plot_drop_callback,
            parent=self.tag,
        )
        dpg.add_plot_legend(parent=self.plot_tag)
        self.plot_x_tag = dpg.add_plot_axis(dpg.mvXAxis, label="Time", parent=self.plot_tag)
        self.plot_y_tag = dpg.add_plot_axis(dpg.mvYAxis, label="Data", parent=self.plot_tag)

        with dpg.handler_registry():
            dpg.add_key_release_handler(
                key=dpg.mvKey_Spacebar, callback=self.toggle_axis_move, user_data=self.plot_tag
            )

    def type_check(self, series_tag, msg_type, puuid, msg):
        if not PlotUitls.is_plot_supported(msg_type):
            print(f"Unknown msg_type: {msg_type}")
            del self.subscriber_func[f"{series_tag}_{puuid}"]
            return
        try:
            if msg_type in TypeParams.PYTHON_TYPES:
                real_msg = pickle.loads(msg)
            else:
                real_msg = TypeParams.TBK_TYPES[msg_type]
                real_msg.ParseFromString(msg)
        except Exception as e:
            uilogger.error("Deserialization failed, please check the data!")
            del self.subscriber_func[f"{series_tag}_{puuid}"]
            return
        return real_msg

    def subscriber_msg(self, msg, user_data):
        series_tag, msg_type, puuid = user_data

        real_msg = self.type_check(series_tag, msg_type, puuid, msg)
        real_msg = PlotUitls.tbkdata2plotdata(real_msg, msg_type)

        if series_tag not in self.subscription_data:
            self.subscription_data[series_tag] = {
                "time": TimedDeque(max_age_seconds=self.max_save_time),
                "data": {},
            }
            if not isinstance(msg, (list, tuple)):
                msg = [msg]
            for i in real_msg:
                self.subscription_data[series_tag]["data"][i] = TimedDeque(
                    max_age_seconds=self.max_save_time
                )
                self.series_tag = dpg.add_line_series(
                    x=[0],
                    y=[0],
                    label=f"{series_tag}_{i}",
                    # tag=f"{series_tag}_{i}_line",
                    parent=self.plot_x_tag,
                )

        self.subscription_data[series_tag]["time"].append(
            self.now_time - self.data_start_time
        )
        msg = [msg] if not isinstance(msg, (list, tuple)) else msg

        for key, value in real_msg.items():
            self.subscription_data[series_tag]["data"][key].append(value)
            if self.is_axis_move:
                dpg.configure_item(
                    item=self.series_tag,
                    x=self.subscription_data[series_tag]["time"].get_items(),
                    y=self.subscription_data[series_tag]["data"][key].get_items()
                )

    def plot_drop_callback(self, sender, app_data, user_data):
        name = app_data["name"]
        msg_name = app_data["msg_name"]
        msg_type = app_data["msg_type"]
        puuid = app_data["puuid"]
        series_tag = f"{name}:{msg_name}"
        if series_tag not in self.subscription_data:
            self.subscriber_func[f"{series_tag}_{puuid}"] = tbkpy.Subscriber(
                name,
                msg_name,
                lambda msg: self.subscriber_msg(msg, (series_tag, msg_type, puuid)),
            )

    def update(self):
        self.now_time = time.time()
        if self.is_axis_move:
            dpg.fit_axis_data(self.plot_y_tag)
            dpg.fit_axis_data(self.plot_x_tag)
            dpg.set_axis_limits(
                axis=self.plot_x_tag,
                ymin=self.now_time - self.data_start_time - self.max_save_time,
                ymax=self.now_time - self.data_start_time,
            )
        else:
            dpg.set_axis_limits_auto(self.plot_x_tag)
