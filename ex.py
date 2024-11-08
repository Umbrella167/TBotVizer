#!/usr/local/bin/python3

from contextlib import contextmanager
from typing import Generator, Union
import dearpygui.dearpygui as dpg
import utils.Utils as utils
from api import TBKApi

dpg.create_context()
dpg.setup_dearpygui()
dpg.create_viewport(title="Test", width=500, height=300)


INDENT_STEP = 30    # actually depends on font size
class TABLETREE:
    def __init__(self):
        pass

    def on_row_clicked(self,sender, value, user_data):
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
    def table_tree_node(self,*cells: str, leaf: bool = False) -> Generator[Union[int, str], None, None]:
        table = dpg.top_container_stack()
        cur_level = dpg.get_item_user_data(table) or 0

        node = dpg.generate_uuid()

        with dpg.table_row(user_data=(cur_level, node)) as row:
            with dpg.group(horizontal=True, horizontal_spacing=0):
                dpg.add_selectable(span_columns=False,
                                callback=self.on_row_clicked, user_data=(table, row))
                dpg.add_tree_node(
                    tag=node,
                    label=cells[0],
                    indent=cur_level*INDENT_STEP,
                    selectable=False,
                    leaf=leaf,
                    default_open=True)

            for label in cells[1:]:
                dpg.add_text(label)
        try:
            dpg.set_item_user_data(table, cur_level + 1)
            yield node
        finally:
            dpg.set_item_user_data(table, cur_level)


    def add_table_tree_leaf(self,*cells: str) -> Union[int, str]:
        with self.table_tree_node(*cells, leaf=True) as node:
            pass
        return node
    def build_dpg_tree(self,tree):
        for key, value in tree.items():
            if isinstance(value, dict):
                if 'info' in value and 'type' in value and 'value' in value:
                    tabletree.add_table_tree_leaf(key, value['info'], value['type'], value['value'])
                else:
                    with tabletree.table_tree_node(key, "--", "--", "--"):
                       self.build_dpg_tree(value)
            else:
                tabletree.add_table_tree_leaf(key, "--", "--", str(value))
tabletree = TABLETREE()
tbk = TBKApi.TBKApi()
param_tree = tbk.param_tree
param_tree_depth = utils.get_tree_depth(param_tree)

with dpg.window():
    dpg.set_primary_window(dpg.last_item(), True)
    # We need to adjust padding so that widgets of different types are positioned properly
    with dpg.theme() as table_theme:
        with dpg.theme_component(dpg.mvAll):
            # Frame padding affects vertical positioning of add_text items within the table
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 0)
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
            borders_outerH=True):
        dpg.bind_item_theme(dpg.last_item(), table_theme)

        dpg.add_table_column(label="Param", width_stretch=True)
        dpg.add_table_column(label="Info", width_stretch=True)
        dpg.add_table_column(label="Type", width_stretch=True)
        dpg.add_table_column(label="Value", width_stretch=True)

        tabletree.build_dpg_tree(param_tree)

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()