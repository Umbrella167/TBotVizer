from ui.boxes import Box

class Component(Box):
    # def __init__(self, parent=None, tag=None, sons=None):
    #     super().__init__(tag, sons)
    #     if sons is None:
    #         sons = []
    #     self.parent = parent
    #     self.sons = sons
    #     self.tag = tag
    #
    # def create(self):
    #     pass
    #
    # def show(self):
    #     pass
    #
    # def draw(self):
    #     self.create()
    #     self.show()
    #
    # def on_row_clicked(self):
    #     pass
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
