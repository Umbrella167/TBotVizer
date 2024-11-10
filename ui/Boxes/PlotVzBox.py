import dearpygui.dearpygui as dpg
from ui.Boxes import Box
import tbkpy._core as tbkpy
import pickle
import time
from collections import deque

class PlotVzBox(Box):
    def __init__(self, uidata, tbkdata):
        self
        self.subscriber_func = []
        self.subscription_data = {}
        self.is_axis_move = True
        self.data_start_time = time.time()
        self.max_data_length = 500  # Set the maximum length for data storage

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
        series_tag, start_time = user_data
        msg = pickle.loads(msg)
        print(f"Received message: {msg}")
        if series_tag not in self.subscription_data:
            self.subscription_data[series_tag] = {
                'time': deque(maxlen=self.max_data_length),
                'data': {}
            }

            if isinstance(msg, (list, tuple)):
                for i in range(len(msg)):
                    self.subscription_data[series_tag]['data'][i] = deque(maxlen=self.max_data_length)
                    dpg.add_line_series(x=[0], y=[0], label=f"{series_tag}_{i}", tag=f"{series_tag}_{i}", parent="plotvz_xaxis")
            else:
                self.subscription_data[series_tag]['data'][0] = deque(maxlen=self.max_data_length)

        current_time = time.time() - start_time
        self.subscription_data[series_tag]['time'].append(current_time)

        if not isinstance(msg, (list, tuple)):
            msg = [msg]
        
        for i, value in enumerate(msg):
            self.subscription_data[series_tag]['data'][i].append(value)
            if self.is_axis_move:
                dpg.configure_item(
                    item=f"{series_tag}_{i}",
                    x=list(self.subscription_data[series_tag]['time']),
                    y=list(self.subscription_data[series_tag]['data'][i])
                )
    def plot_drop_callback(self, sender, app_data, user_data):
        _msg = app_data['msg']
        name = app_data['name']
        series_tag = f'{_msg}:{name}_line'

        if series_tag not in self.subscription_data:
            start_time = time.time()
            self.data_start_time = start_time
            self.subscriber_func.append(tbkpy.Subscriber(
                _msg, name, lambda msg: self.subscriber_msg(msg, (series_tag, start_time))
            ))

    def update(self):
        if self.is_axis_move:
            now_time = time.time()
            dpg.fit_axis_data("plotvz_yaxis")
            dpg.fit_axis_data("plotvz_xaxis")
            dpg.set_axis_limits(
                axis="plotvz_xaxis",
                ymin=now_time - self.data_start_time - 10,
                ymax=now_time - self.data_start_time
            )
        else:
            dpg.set_axis_limits_auto("plotvz_xaxis")