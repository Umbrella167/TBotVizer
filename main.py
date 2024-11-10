import os
os.system('export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python')

from tbkpy import _core as tbkpy
tbkpy.init("TBK-Client")


import ui.Ui as ui
import dearpygui.dearpygui as dpg
from api import TBKApi
from ui.box.MessageBox import MessageBox
from ui.box.ParamBox import ParamBox
from ui.box.PlotVzBox import PlotVzBox
from utils.DataProcessor import UiData, TBKData
tbkapi = TBKApi.TBKApi()
tbkdata = TBKData(tbkapi)
uidata = UiData()
t_pbox = ParamBox(uidata, tbkdata)
t_msgbox = MessageBox(uidata, tbkdata)
t_plotvzbox = PlotVzBox(uidata, tbkdata)
boxes = [t_pbox, t_msgbox,t_plotvzbox]
UI = ui.UI(uidata, boxes)
def loop():
    try:
        UI.update()
    except Exception as e:
        print(e)
        print("loop failed")

def main():
    dpg.create_context()
    UI._theme.set_theme("Dark")
    UI._theme.set_font(20)
    UI.draw()
    UI.create_viewport()
    UI.show_ui()
    UI.run_loop(loop)
if __name__ == "__main__":
    main()
