import dearpygui.dearpygui as dpg


# create a fonction who can dectect if the position A is hover the dpg item
def is_hovered(item_id, pos):
    return dpg.is_item_hovered(item_id, pos)