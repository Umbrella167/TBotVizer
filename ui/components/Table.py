import dearpygui.dearpygui as dpg


class Table:
    def __init__(self, cols_title=None, **kwargs):
        super().__init__(**kwargs)
        if cols_title is None:
            cols_title = []
        self.rows = []
        self.cells = []
        self.tag_table = []
        self.cols_title = cols_title

    def create(self):
        self.tag = dpg.add_table(
            header_row=True,
            policy=dpg.mvTable_SizingFixedFit,
            row_background=True,
            reorderable=True,
            resizable=True,
            no_host_extendX=False,
            hideable=True,
            borders_innerV=True,
            delay_search=True,
            borders_outerV=True,
            borders_innerH=True,
            borders_outerH=True,
            parent=self.parent.tag,
        )
        self.is_created = True
        for l in self.cols_title:
            dpg.add_table_column(label=l, width_fixed=True, parent=self.tag)

    def create_cols(self):
        """
        tbk_data
        {
        {{}, {}, {}},
        {{},{}},
        {{},{},{},{}},
        }
        """


        """
        "text": add_text        
        
        dic["text"]()
        
        {
        {
        "type": "text"
        "config": {""}
        }
        
        }
        
        """
        for line in self.tbk_data:
            row_tag = dpg.add_table_row(parent=self.tag)
            self.rows.append(row_tag)
            t_row = []
            for cell_data in line:
                cell_tag = dpg.add_text(default_value=cell_data, parent=row_tag)
                self.cells.append(cell_tag)
                t_row.append(cell_tag)
            self.tag_table.append(t_row)

            # for row_index, (param, value) in enumerate(self.tbk_data._param_data.items()):
        #         with dpg.table_row(parent=table_tag, tag=param):
        #             dpg.add_text(default_value=param, tag=param + "_param")
        #             _info = value["info"]
        #             _type = value["type"]
        #             for item in value:
        #                 if item == "value":
        #                     tag = param + "_" + item
        #                     StrInput(tbk_data=TypeParams(), tbkdata=self.tbk_data).new_input(
        #                         tag=tag,
        #                         value=value[item],
        #                         type=_type,
        #                         info=_info,
        #                         parent=param,
        #                     )
        #                     # 如果值是空的,那么设置为红色
        #                     if value[item] == "None":
        #                         set_input_color(tag, [255, 0, 0, 255])
        #                 else:
        #                     dpg.add_text(default_value=value[item], tag=param + "_" + item)
