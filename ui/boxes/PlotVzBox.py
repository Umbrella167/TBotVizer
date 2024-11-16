import dearpygui.dearpygui as dpg
import time

from google.protobuf.json_format import MessageToDict
from loguru import logger as uilogger
from static.Params import TypeParams
from ui.boxes.BaseBox import Box
from utils.Utils import msg_serializer
from utils.DataProcessor import tbk_data


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
            if data_type == "int" or data_type == "float":
                res = {"0": data}
            elif data_type == "list" or data_type == "tuple":
                res = {}
                for i in range(len(data)):
                    res[str(i)] = data[i]
            else:
                res = data
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
        while (
            self.items_with_timestamps
            and (current_time - self.items_with_timestamps[0][1]) > self.max_age_seconds
        ):
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
        self.only = False
        self.series_tag = None
        self.plot_tag = None
        self.series_tags = {}
        self.plot_x_tag = None
        self.plot_y_tag = None
        self.message_subscriber_dict = {}
        self.subscriber_func = {}
        self.subscription_data = {}
        self.is_axis_move = True
        self.data_start_time = time.time()
        self.now_time = time.time()
        self.max_save_time = 5  # 数据保存的最大时间限制
        self.checkbox_bind = {}

    def toggle_axis_move(self, sender, app_data, user_data):
        # 检测到空格则停止移动x轴
        box_tag = user_data
        if not dpg.is_item_focused(box_tag):
            return
        self.is_axis_move = not self.is_axis_move

    def create(self):
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
            # drop_callback=self.plot_drop_callback,
            drop_callback=self.plot_drop_callback,
            parent=self.tag,
        )
        dpg.add_plot_legend(parent=self.plot_tag)
        self.plot_x_tag = dpg.add_plot_axis(
            dpg.mvXAxis, label="Time", parent=self.plot_tag
        )
        self.plot_y_tag = dpg.add_plot_axis(
            dpg.mvYAxis, label="Data", parent=self.plot_tag
        )

        with dpg.handler_registry():
            dpg.add_key_release_handler(
                key=dpg.mvKey_Spacebar,
                callback=self.toggle_axis_move,
                user_data=self.plot_tag,
            )

    def subscriber_msg(self, msg, user_data):
        puuid, name, msg_name, msg_type, series_tag = user_data
        try:
            real_msg = msg_serializer(msg, msg_type)
        except Exception as e:
            del self.message_subscriber_dict[puuid][msg_name][name]
            print(f"Deserialization failed, please check the data! {e}")
            return

        real_msg = PlotUitls.tbkdata2plotdata(real_msg, msg_type)

        if series_tag not in self.subscription_data:
            # 如果该词条未被创建, 则新建词条
            self.subscription_data[series_tag] = {
                "time": TimedDeque(max_age_seconds=self.max_save_time),
                "data": {},
            }
            if not isinstance(msg, (list, tuple)):
                msg = [msg]
            self.series_tags[series_tag] = {}
            for i in real_msg:
                self.subscription_data[series_tag]["data"][i] = TimedDeque(
                    max_age_seconds=self.max_save_time
                )
                # 添加标签(这个标签可能有多个)
                self.series_tags[series_tag][i] = dpg.add_line_series(
                    x=[0],
                    y=[0],
                    parent=self.plot_x_tag,
                )

        # 更新数据
        self.subscription_data[series_tag]["time"].append(
            self.now_time - self.data_start_time
        )
        msg = [msg] if not isinstance(msg, (list, tuple)) else msg
        for key, value in real_msg.items():
            self.subscription_data[series_tag]["data"][key].append(value)
            if self.is_axis_move:
                dpg.configure_item(
                    item=self.series_tags[series_tag][key],
                    x=self.subscription_data[series_tag]["time"].get_items(),
                    y=self.subscription_data[series_tag]["data"][key].get_items(),
                )
        # 更新图例label，主要是label可能会太长，作简略显示
        for key, _ in real_msg.items():
            t_label = ""
            if len(self.message_subscriber_dict) > 1:
                tpuuid = puuid
                if len(puuid) > 8:
                    tpuuid = puuid[:4]+"..."+puuid[-4:]
                t_label += tpuuid + ":"
            t_label += f"{msg_name}({name}):{key}"
            dpg.configure_item(self.series_tags[series_tag][key], label=t_label)

    def plot_drop_callback(self, sender, app_data):
        msg_info, msg_checkbox_tag = app_data
        msg_type = msg_info["msg_type"]
        sub_checkbox = msg_checkbox_tag["sub_checkbox"]
        if not dpg.get_value(sub_checkbox):
            return
        if not PlotUitls.is_plot_supported(msg_type):
            print(f"Unknown msg_type: {msg_type}")
            return

        name = msg_info["name"]
        msg_name = msg_info["msg_name"]
        puuid = msg_info["puuid"]
        message_data = f"{puuid}_{msg_name}:{name}"
        series_tag = f"{puuid}:{msg_name}:{name}"
        self.checkbox_bind[sub_checkbox] = (series_tag,puuid, msg_name, name)
        if puuid not in self.message_subscriber_dict:
            # 如果节点不在表内则添加该节点进表
            self.message_subscriber_dict[puuid] = {}

        if msg_name not in self.message_subscriber_dict[puuid]:
            # 如果消息不在表内，则添加消息进表
            self.message_subscriber_dict[puuid][msg_name] = {}

        if name not in self.message_subscriber_dict[puuid][msg_name]:
            # 如果消息不在表内则添加消息进表
            msg_info["tag"] = self.tag
            self.message_subscriber_dict[puuid][msg_name][name] = tbk_data.Subscriber(
                msg_info,
                lambda msg: self.subscriber_msg(
                    msg, (puuid, name, msg_name, msg_type, series_tag)
                ),
            )
            return
        print(f"{message_data}已绘制")

    def __(self):
        for tag in self.checkbox_bind:
            series_tag_dict,puuid, msg_name, name = self.checkbox_bind[tag]

            if not dpg.get_value(tag):
                if series_tag_dict in self.series_tags:
                    for series_tag in self.series_tags[series_tag_dict].values():
                        dpg.delete_item(series_tag)
                    del self.subscription_data[series_tag_dict]
                    del self.series_tags[series_tag_dict]
                    del self.message_subscriber_dict[puuid][msg_name][name]
                    
    def update(self):
        self.now_time = time.time()
        self.__()
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
