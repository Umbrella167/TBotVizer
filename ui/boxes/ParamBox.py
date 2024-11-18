import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from utils.ClientLogManager import client_logger
from utils.DataProcessor import tbk_data


class ParamBaseBox(BaseBox):
    only = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tbk_data = tbk_data
        self.data = {}
        self.table_tag = None

        self.tb = None
        self.table_title = ["Param", "Info", "Type", "Value"]
        self.row_tags = {}

    def create(self):
        self.check_and_create_window()

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
        for t in self.table_title:
            dpg.add_table_column(label=t, width_fixed=True, parent=self.table_tag)

    # 更新表格中内容
    def update(self):
        new_data = self.tbk_data.param_data
        # 如果数据没有变化，则不更新
        if self.data == new_data:
            return
        # 将现有数据和新数据转换为集合，便于比较
        current_params = set(self.data.keys())
        new_params = set(new_data.keys())
        # 找到需要删除的行（即在current而不在new中的参数）
        params_to_delete = current_params - new_params
        # 找到需要新增的行（即在new而不在current中的参数）
        params_to_add = new_params - current_params
        # 删除不需要的数据行
        for param in params_to_delete:
            row_tag = self.row_tags[param]
            dpg.delete_item(row_tag)
            del self.row_tags[param]
        # 添加新的数据行
        for param in params_to_add:
            value = new_data[param]
            row_tag = dpg.add_table_row(parent=self.table_tag)
            self.row_tags[param] = row_tag
            dpg.add_text(default_value=param, parent=row_tag)
            for item in value:
                cell_tag = dpg.add_text(default_value=value[item], parent=row_tag)
        # 更新现有的行
        for param in current_params.intersection(new_params):
            if self.data.get(param) == new_data[param]:
                # 如果值相同则不更新
                continue
            row_tag = self.row_tags[param]
            # 更新每个单元格的内容
            value = new_data[param]
            for cell_index, (key, cell_value) in enumerate(value.items()):
                cell_tag = dpg.get_item_children(row_tag)[1][cell_index + 1]
                dpg.set_value(cell_tag, cell_value)
        # 更新完后将当前数据保存
        client_logger.log("INFO", "ParamBaseBox updated!")
        self.data = new_data.copy()

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

        # self.tb = Table(table_title=self.table_title, parent=self, tbk_data=self.tbk_data)

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
    #         # 这句暂时有点问题
    #         # dpg.set_value(k + '_value', v['value'])
    #         pass
