import os
os.system('export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python')

from tbkpy import _core as tbkpy
tbkpy.init("TBK-Client")


import ui.Ui as ui
import dearpygui.dearpygui as dpg
from api import TBKApi
from ui.Boxes.MessageBox import MessageBox
from ui.Boxes.ParamBox import ParamBox
from utils.DataProcessor import TBKData
from ui.Boxes.PlotVzBox import PlotVzBox
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
    layout_manager = LayoutManager()

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
