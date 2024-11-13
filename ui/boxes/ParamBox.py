import dearpygui.dearpygui as dpg

from static.Params import TypeParams
from ui.boxes import Box
from ui.components.Input import Input
from utils.Utils import set_input_color


class ParamBox(Box):
    def draw(self):
        with dpg.window(tag="param_window", label="Param", no_collapse=True):
            # 创建新的表格
            with dpg.table(
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
                    parent="param_window",
            ) as table_tag:
                # 添加表格列
                dpg.add_table_column(label="Param", width_fixed=True, parent=table_tag)
                dpg.add_table_column(label="Info", width_fixed=True, parent=table_tag)
                dpg.add_table_column(label="Type", width_fixed=True, parent=table_tag)
                dpg.add_table_column(label="Value", width_fixed=True, parent=table_tag)
                # table_tree = self._diycomponents.TableTree()
                # table_tree.build_dpg_tree(self.tbk_data.param_tree)
                # 添加表格行和内容
                print(self.tbk_data.param_data)
                for row_index, (param, value) in enumerate(self.tbk_data.param_data.items()):
                    with dpg.table_row(parent=table_tag, tag=param):
                        dpg.add_text(default_value=param, tag=param + "_param")
                        _info = value["info"]
                        _type = value["type"]
                        for item in value:
                            if item == "value":
                                tag = param + "_" + item
                                Input(data=TypeParams(), tbkdata=self.tbk_data).new_input(
                                    tag=tag,
                                    value=value[item],
                                    type=_type,
                                    info=_info,
                                    parent=param,
                                )
                                # self._diycomponents.Input(outer_instance=self._diycomponents, data=self._type_params,
                                #                           tbk_data=self.tbk_data).new_input(
                                #     tag=tag,
                                #     value=value[item],
                                #     type=_type,
                                #     info=_info,
                                #     parent=param,
                                # )

                                # 如果值是空的,那么设置为红色
                                if value[item] == "None":
                                    set_input_color(tag, [255, 0, 0, 255])
                            else:
                                dpg.add_text(default_value=value[item], tag=param + "_" + item)

    # TODO： 只会更改已有的条目，无法插入新数据，也没有做类型的检查，如果类型错误则会报错
    def update(self):
        for k, v in self.tbk_data.param_data.items():
            # print('k: ',k)
            # print('v: ',v)

            # 这句暂时有点问题
            # dpg.set_value(k + '_value', v['value'])
            pass
