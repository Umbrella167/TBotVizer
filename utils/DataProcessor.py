class UiData:
    def __init__(self):
        # 初始化变量
        self.draw_mouse_pos = (0, 0)
        self.draw_mouse_pos_last = (0, 0)
        self.mouse_move_pos = (0, 0)

_ui_data_instance = None


def get_ui_data():
    global _ui_data_instance
    if _ui_data_instance is None:
        _ui_data_instance = UiData()
    return _ui_data_instance
