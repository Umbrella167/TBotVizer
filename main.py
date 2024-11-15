# export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
from dearpygui.demo import show_demo

import ui.Ui as ui
from api import TBKApi
from config.UiConfig import UiConfig
from ui.boxes.ComboBoxDemo import ComboBoxDemo
from ui.boxes.MessageBox import MessageBox
from ui.boxes.ParamBox import ParamBox
from utils.DataProcessor import TBKData
from ui.boxes.PlotVzBox import PlotVzBox
from ui.boxes.CanvasBox import CanvasBox
from ui.boxes.ConsoleBox import ConsoleBox


def loop(UI):
    try:
        UI.update()
    except Exception as e:
        print(e)
        print("loop failed")


def main():
    dpg.create_context()



    t_pbox = ParamBox()
    t_msgbox = MessageBox(tag="test")
    t_canvas_box = CanvasBox()
    t_plot_vz_box = PlotVzBox(tag="plot_vz_window")


    l = ["Option 1", "Option 2", "Option 3", "Option 4"]
    t_cbd = ComboBoxDemo(data=l)

    boxes = [t_pbox, t_msgbox, t_plot_vz_box, t_cbd, t_canvas_box]
    # boxes = [ConsoleBox()]

    demo.show_demo()

    UI = ui.UI(boxes=boxes)

    UI.show()
    # UI.create()

    UI.run_loop(lambda: loop(UI))

if __name__ == "__main__":
    main()
