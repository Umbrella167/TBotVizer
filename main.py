# export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
import dearpygui.dearpygui as dpg

import ui.Ui as ui
from utils.ClientLogManager import ClientLogManager, client_logger


def loop(UI):
    try:
        UI.update()
    except Exception as e:
        client_logger.log("ERROR", f"Loop Failed! {e}")


def main():
    dpg.create_context()

    UI = ui.UI()

    UI.show()

    UI.run_loop(lambda: loop(UI))



if __name__ == "__main__":
    main()
