# export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
import dearpygui.dearpygui as dpg

import ui.Ui as ui
from api import TBKApi
from config.UiConfig import UiConfig
from ui.boxes.MessageBox import MessageBox
from ui.boxes.ParamBox import ParamBox
from utils.DataProcessor import TBKData
from ui.boxes.PlotVzBox import PlotVzBox

def loop(UI):
    try:
        UI.update()
    except Exception as e:
        print(e)
        print("loop failed")


def main():
    dpg.create_context()

    tbk_api = TBKApi.TBKApi()
    tbk_data = TBKData(tbk_api)

    t_pbox = ParamBox(tbk_data)
    t_msgbox = MessageBox(tbk_data)
    t_plotvzbox = PlotVzBox()
    boxes = [t_pbox, t_msgbox, t_plotvzbox]


    ui_config = UiConfig(boxes=boxes)
    UI = ui.UI(ui_config)

    # UI.config.layout.set_theme("Dark")
    # UI.config.layout.set_font(20)

    UI.draw()
    UI.show()

    UI.run_loop(lambda: loop(UI))


if __name__ == "__main__":
    main()
