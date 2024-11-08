import ui.Ui as ui
import dearpygui.dearpygui as dpg
from api import TBKApi
from ui.box.MessageBox import MessageBox
from ui.box.ParamBox import ParamBox
from utils.DataProcessor import UiData, TBKData

tbkapi = TBKApi.TBKApi()
tbkdata = TBKData(tbkapi)
uidata = UiData()

t_pbox = ParamBox(uidata, tbkdata)
t_msgbox = MessageBox(uidata, tbkdata)
boxes = [t_pbox, t_msgbox]

UI = ui.UI(uidata, boxes)

def loop():
    try:
        UI.update()
        # tbkapi.update_param()
        # tbkapi.update_message()
        # UI.update_param_data()
        # UI.update_param_data2()
        # UI.update_message_list2()
    except Exception as e:
        print(e)
        print("loop failed")


def main():
    dpg.create_context()
    UI._theme.set_theme("Dark")
    UI._theme.set_font(20)
    # 创建参数窗口
    # UI.create_param_window()
    # UI.create_param_window2()
    # 创建消息窗口
    # UI.create_message_window()
    # UI.create_message_window2()
    UI.draw()

    UI.create_viewport()
    UI.show_ui()
    UI.run_loop(loop)


if __name__ == "__main__":
    main()
