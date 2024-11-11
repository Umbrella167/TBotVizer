import os

from config.SystemConfig import config

os.system('export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python')

import ui.Ui as ui
import dearpygui.dearpygui as dpg
from api import TBKApi
from ui.boxes.MessageBox import MessageBox
from ui.boxes.ParamBox import ParamBox
from utils.DataProcessor import TBKData
from ui.boxes.PlotVzBox import PlotVzBox
from ui.LayoutManager import LayoutManager

def loop(UI):
    try:
        UI.update()
    except Exception as e:
        print(e)
        print("loop failed")


def main():
    tbk_api = TBKApi.TBKApi()
    tbk_data = TBKData(tbk_api)
    layout_manager = LayoutManager(config.UI_LAYOUT_FILE)
    t_pbox = ParamBox(layout_manager, tbk_data)
    t_msgbox = MessageBox(layout_manager, tbk_data)
    t_plotvzbox = PlotVzBox(layout_manager, tbk_data)
    boxes = [t_pbox, t_msgbox, t_plotvzbox]

    UI = ui.UI(layout_manager, boxes)

    dpg.create_context()
    UI.Layout.set_theme("Dark")
    UI.Layout.set_font(20)
    UI.draw()

    # UI.show()
    UI.run_loop(lambda: loop(UI))

if __name__ == "__main__":
    main()
