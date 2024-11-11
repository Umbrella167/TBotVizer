import dearpygui.dearpygui as dpg
from ui.boxes import Box
from collections import deque
import tbkpy._core as tbkpy
import pickle
import time

class TimedDeque:
    def __init__(self, max_age_seconds):
        self.deque = deque()
        self.max_age_seconds = max_age_seconds

    def append(self, item):
        # 添加元素和当前时间戳
        self.deque.append((item, time.time()))
        self._remove_old_items()

    def _remove_old_items(self):
        # 移除超过时间限制的元素
        current_time = time.time()
        while self.deque and (current_time - self.deque[0][1]) > self.max_age_seconds:
            self.deque.popleft()

    def __iter__(self):
        # 迭代元素，忽略时间戳
        return (item for item, _ in self.deque)

    def __len__(self):
        # 返回元素数量
        return len(self.deque)

class PlotVzBox:
    def __init__(self, uidata, tbkdata):
        self.subscriber_func = []
        self.subscription_data = {}
        self.is_axis_move = True
        self.data_start_time = time.time()
        self.now_time = time.time()
        self.max_save_time = 10  # 数据保存的最大时间限制
    def toggle_axis_move(self):
        self.is_axis_move = not self.is_axis_move

    def draw(self):
        with dpg.window(label='Plot Visualizer', tag="plotvz_window"):
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
                dpg.add_plot_axis(dpg.mvXAxis, label='Time', tag="plotvz_xaxis")
                dpg.add_plot_axis(dpg.mvYAxis, label='Data', tag="plotvz_yaxis")

        with dpg.handler_registry():
            dpg.add_key_release_handler(key=dpg.mvKey_Spacebar, callback=self.toggle_axis_move)

    def subscriber_msg(self, msg, user_data):
        series_tag = user_data
        msg = pickle.loads(msg)
        if series_tag not in self.subscription_data:
            self.subscription_data[series_tag] = {
                'time': TimedDeque(max_age_seconds=self.max_save_time),
                'data': {}
            }

            if not isinstance(msg, (list, tuple)):
                msg = [msg]
            for i in range(len(msg)):
                self.subscription_data[series_tag]['data'][i] = TimedDeque(max_age_seconds=self.max_save_time)
                dpg.add_line_series(x=[0], y=[0], label=f"{series_tag}_{i}", tag=f"{series_tag}_{i}_line", parent="plotvz_xaxis")

        self.subscription_data[series_tag]['time'].append(self.now_time - self.data_start_time)

        if not isinstance(msg, (list, tuple)):
            msg = [msg]
        
        for i, value in enumerate(msg):
            self.subscription_data[series_tag]['data'][i].append(value)
            if self.is_axis_move:
                dpg.configure_item(
                    item=f"{series_tag}_{i}_line",
                    x=list(self.subscription_data[series_tag]['time']),
                    y=list(self.subscription_data[series_tag]['data'][i])
                )

    def plot_drop_callback(self, sender, app_data, user_data):
        _msg = app_data['msg']
        name = app_data['name']
        series_tag = f'{_msg}:{name}'

        if series_tag not in self.subscription_data:
            self.subscriber_func.append(tbkpy.Subscriber(
                _msg, name, lambda msg: self.subscriber_msg(msg, series_tag)
            ))

    def update(self):
        self.now_time = time.time()
        if self.is_axis_move:
            dpg.fit_axis_data("plotvz_yaxis")
            dpg.fit_axis_data("plotvz_xaxis")
            dpg.set_axis_limits(
                axis="plotvz_xaxis",
                ymin= self.now_time - self.data_start_time - self.max_save_time,
                ymax= self.now_time - self.data_start_time
            )
        else:
            dpg.set_axis_limits_auto("plotvz_xaxis")