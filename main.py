# export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
import dearpygui.dearpygui as dpg
from numpy.core.defchararray import title

import ui.Ui as ui
from api import TBKApi
from config.UiConfig import UiConfig
from ui.boxes.ComboBoxDemo import ComboBoxDemo
from ui.boxes.MessageBox import MessageBox
from ui.boxes.ParamBox import ParamBox
from utils.DataProcessor import TBKData
from ui.boxes.PlotVzBox import PlotVzBox
def loop(UI):
    try:
        UI.update()
        print(dpg.get_frame_rate())
    except Exception as e:
        print(e)
        print("loop failed")


def main():
    dpg.create_context()

    tbk_api = TBKApi.TBKApi()
    tbk_data = TBKData(tbk_api)

    t_pbox = ParamBox(tbk_data=tbk_data)
    t_msgbox = MessageBox(tbk_data=tbk_data)
    t_plotvzbox = PlotVzBox()


    l = ["Option 1", "Option 2", "Option 3", "Option 4"]
    t_cbd = ComboBoxDemo(data=l)

    boxes = [t_pbox, t_msgbox, t_plotvzbox, t_cbd]


    ui_config = UiConfig(boxes=boxes)
    UI = ui.UI(ui_config)

    # UI.config.layout.set_theme("Dark")
    # UI.config.layout.set_font(20)

    UI.show()
    # UI.create()

    UI.run_loop(lambda: loop(UI))

if __name__ == "__main__":
    main()
