from ui.LayoutManager import LayoutManager


class UiConfig():
    def __init__(self, title="TBK-ParamManager"):
        # TODO: 长宽应该根据系统长宽设定
        super().__init__()
        self.layout = LayoutManager()
        self.title = title
        self.instance = None

UI_TITTLE = "TBK-ParamManager"