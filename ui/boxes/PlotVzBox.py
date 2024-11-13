import dearpygui.dearpygui as dpg
from collections import deque
import tbkpy._core as tbkpy
import time
from static.Params import TypeParams
from google.protobuf.json_format import MessageToDict
from loguru import logger as uilogger
import pickle
class PlotUitls:
    @staticmethod
    def is_plot_supported(tbk_type):
        if tbk_type not in TypeParams.PLOT_SUPPORT_TYPES:
            return False
        return True
    @staticmethod
    def tbkdata2plotdata(data,data_type):
        if not PlotUitls.is_plot_supported(data_type):
            uilogger.error("Unsupported data type")
            return 
        if data_type in TypeParams.PYTHON_TYPES:
            if data_type == 'int' or data_type == 'float':
                res = {'0':data}
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

# class TimedDeque:
#     def __init__(self, max_age_seconds):
#         self.deque = deque()
#         self.max_age_seconds = max_age_seconds

#     def append(self, item):
#         # 添加元素和当前时间戳
#         self.deque.append((item, time.time()))
#         self._remove_old_items()

#     def _remove_old_items(self):
#         # 移除超过时间限制的元素
#         current_time = time.time()
#         while self.deque and (current_time - self.deque[0][1]) > self.max_age_seconds:
#             self.deque.popleft()

#     def __iter__(self):
#         # 迭代元素，忽略时间戳
#         return (item for item, _ in self.deque)

#     def __len__(self):
#         # 返回元素数量
#         return len(self.deque)
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

class PlotVzBox:
    def __init__(self):
        self.subscriber_func = {}
        self.subscription_data = {}
        self.is_axis_move = True
        self.data_start_time = time.time()
        self.now_time = time.time()
        self.max_save_time = 5  # 数据保存的最大时间限制

    def toggle_axis_move(self):
        self.is_axis_move = not self.is_axis_move
    def draw(self):
        with dpg.window(label="Plot Visualizer", tag="plotvz_window"):
            dpg.add_text("Plot Visualizer")

            with dpg.plot(
                tag="plotvz_plot",
                width=-1,
                height=-1,
                label="Plot Tools",
                payload_type="plot_data",
                drop_callback=self.plot_drop_callback,
            ):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="plotvz_xaxis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Data", tag="plotvz_yaxis")

        with dpg.handler_registry():
            dpg.add_key_release_handler(
                key=dpg.mvKey_Spacebar, callback=self.toggle_axis_move
            )
    

    def type_check(self, series_tag, msg_type, puuid,msg):
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

        real_msg = self.type_check(series_tag, msg_type, puuid,msg)
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
                dpg.add_line_series(
                    x=[0],
                    y=[0],
                    label=f"{series_tag}_{i}",
                    tag=f"{series_tag}_{i}_line",
                    parent="plotvz_xaxis",
                )

        self.subscription_data[series_tag]["time"].append(
            self.now_time - self.data_start_time
        )
        msg = [msg] if not isinstance(msg, (list, tuple)) else msg

        for key, value in real_msg.items():
            self.subscription_data[series_tag]["data"][key].append(value)
            if self.is_axis_move:
                # print(self.subscription_data[series_tag]["time"])
                dpg.configure_item(
                    item=f"{series_tag}_{key}_line",
                    # x=list(self.subscription_data[series_tag]["time"]),
                    # y=list(self.subscription_data[series_tag]["data"][key]),
                    x = self.subscription_data[series_tag]["time"].get_items(),
                    y = self.subscription_data[series_tag]["data"][key].get_items()
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

            # self.subscriber_func.append(tbkpy.Subscriber(
            #     name, msg_name, lambda msg: self.subscriber_msg(msg, (series_tag,msg_type))
            # ))

    def update(self):
        self.now_time = time.time()
        if self.is_axis_move:
            dpg.fit_axis_data("plotvz_yaxis")
            dpg.fit_axis_data("plotvz_xaxis")
            dpg.set_axis_limits(
                axis="plotvz_xaxis",
                ymin=self.now_time - self.data_start_time - self.max_save_time,
                ymax=self.now_time - self.data_start_time,
            )
        else:
            dpg.set_axis_limits_auto("plotvz_xaxis")
