import dearpygui.dearpygui as dpg

from ui.boxes import Box


class ParamBox(Box):
    def __init__(self, tbk_data, **kwargs):
        super().__init__(**kwargs)
        self.tbk_data = tbk_data
        self.table_tag = None
        
        self.tb = None
        self.cols_title = ["Param", "Info", "Type", "Value"]
        self.tags = []

    def create(self):
        if self.tag:
            dpg.add_window(tag=self.tag, label=self.label)
        else:
            self.tag = dpg.add_window(label=self.label)

        if self.label is None:
            dpg.configure_item(self.tag, label="Param_box")
        # 添加表格
        self.table_tag = dpg.add_table(
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
            parent=self.tag,
        )
        # 表格标题
        for t in self.cols_title:
            dpg.add_table_column(label=t, width_fixed=True, parent=self.table_tag)
        # 插入表格内容
        self.tags = self.insert_row(self.tbk_data.param_data)

    def insert_row(self, data):
        # 返回整个表的tag表
        t_table = []
        for row_index, (param, value) in enumerate(data.items()):
            # 创建行
            t_row = []
            row_tag = dpg.add_table_row(parent=self.table_tag)
            dpg.add_text(default_value=param, parent=row_tag)
            for item in value:
                # 创建单元格
                cell_tag = dpg.add_text(default_value=value[item], parent=row_tag)
                t_row.append(cell_tag)
            t_table.append(t_row)
        return t_table
    
    
        # _info = value["info"]
        # _type = value["type"]
        # for item in value:
        #     if item == "value":
        #         tag = param + "_" + item
        #         Input(data=TypeParams(), tbkdata=self.tbk_data).new_input(
        #             tag=tag,
        #             value=value[item],
        #             type=_type,
        #             info=_info,
        #             parent=param+"_param",
        #         )
        #         # 如果值是空的,那么设置为红色
        #         if value[item] == "None":
        #             set_input_color(tag, [255, 0, 0, 255])
        #     else:
        #         dpg.add_text(default_value=value[item], tag=param + "_" + item)

        # self.tb = Table(cols_title=self.cols_title, parent=self, tbk_data=self.tbk_data)

        # # 创建新的表格
        # with dpg.table(
        #         header_row=True,
        #         policy=dpg.mvTable_SizingFixedFit,
        #         row_background=True,
        #         reorderable=True,
        #         resizable=True,
        #         no_host_extendX=False,
        #         hideable=True,
        #         borders_innerV=True,
        #         delay_search=True,
        #         borders_outerV=True,
        #         borders_innerH=True,
        #         borders_outerH=True,
        #         parent="param_window",
        # ) as table_tag:
        #     # 添加表格列
        #     dpg.add_table_column(label="Param", width_fixed=True, parent=table_tag)
        #     dpg.add_table_column(label="Info", width_fixed=True, parent=table_tag)
        #     dpg.add_table_column(label="Type", width_fixed=True, parent=table_tag)
        #     dpg.add_table_column(label="Value", width_fixed=True, parent=table_tag)
        #     # 添加表格行和内容
        #
        #
        #     for row_index, (param, value) in enumerate(self.tbk_data.param_data.items()):
        #         with dpg.table_row(parent=table_tag, tag=param):
        #             dpg.add_text(default_value=param, tag=param + "_param")
        #             _info = value["info"]
        #             _type = value["type"]
        #             for item in value:
        #                 if item == "value":
        #                     tag = param + "_" + item
        #                     Input(tbk_data=TypeParams(), tbkdata=self.tbk_data).new_input(
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

    # TODO： 只会更改已有的条目，无法插入新数据，也没有做类型的检查，如果类型错误则会报错
    # def update(self):
    #     for k, v in self.tbk_data.param_data.items():
    #         # print('k: ',k)
    #         # print('v: ',v)
    #
    #         # 这句暂时有点问题
    #         # dpg.set_value(k + '_value', v['value'])
    #         pass
