from ui.Components import component
from dearpygui import dearpygui as dpg
from contextlib import contextmanager
from typing import Generator, Union

"""
这个类还没用到，也没做测试
"""

class TableTree(component):
    def __init__(self):
        self.param_tag = ""

    def on_row_clicked(self, sender, value, user_data):
        # Make sure it happens quickly and without flickering
        with dpg.mutex():
            # We don't want to highlight the selectable as "selected"
            dpg.set_value(sender, False)

            table, row = user_data
            root_level, node = dpg.get_item_user_data(row)

            # First of all let's toggle the node's "expanded" status
            is_expanded = not dpg.get_value(node)
            dpg.set_value(node, is_expanded)
            # All children *beyond* this level (but not on this level) will be hidden
            hide_level = 10000 if is_expanded else root_level

            # Now manage the visibility of all the children as necessary
            rows = dpg.get_item_children(table, slot=1)
            root_idx = rows.index(row)
            # We don't want to look at rows preceding our current "root" node
            rows = rows[root_idx + 1:]
            for child_row in rows:

                child_level, child_node = dpg.get_item_user_data(child_row)
                if child_level <= root_level:
                    break

                if child_level > hide_level:
                    dpg.hide_item(child_row)
                else:
                    dpg.show_item(child_row)
                    hide_level = 10000 if dpg.get_value(
                        child_node) else child_level

    @contextmanager
    def table_tree_node(self, *cells: str, leaf: bool = False, tag=0) -> Generator[Union[int, str], None, None]:
        table = dpg.top_container_stack()
        cur_level = dpg.get_item_user_data(table) or 0

        node = dpg.generate_uuid()
        INDENT_STEP = 30
        with dpg.table_row(user_data=(cur_level, node)) as row:
            with dpg.group(horizontal=True, horizontal_spacing=0):
                span_columns = True if cells[1] == "--" else False
                dpg.add_selectable(span_columns=span_columns,
                                   callback=self.on_row_clicked, user_data=(table, row))
                dpg.add_tree_node(
                    tag=node,
                    label=cells[0],
                    # indent=cur_level*INDENT_STEP,
                    selectable=False,
                    leaf=leaf,
                    default_open=True)

            for label in cells[1:]:
                # print(label)
                dpg.add_text(label, tag=tag)
        try:
            dpg.set_item_user_data(table, cur_level + 1)
            yield node
        finally:
            dpg.set_item_user_data(table, cur_level)

    def add_table_tree_leaf(self, *cells: str, tag=0) -> Union[int, str]:
        with self.table_tree_node(*cells, leaf=True, tag=tag) as node:
            pass
        return node

    def build_dpg_tree(self, tree):
        for key, value in tree.items():
            if isinstance(value, dict):
                if 'info' in value and 'type' in value and 'value' in value:
                    print(value['info'], value['type'], value['value'])
                    self.add_table_tree_leaf(key, value['info'], value['type'], value['value'])
                else:
                    with self.table_tree_node(key, "--", "--", "--"):
                        self.build_dpg_tree(value)
                        # self.param_tag = self.param_tag + "/" + value
            else:
                print(key)

                self.add_table_tree_leaf(key, "--", "--", str(value))