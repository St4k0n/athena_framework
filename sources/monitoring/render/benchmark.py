import pyglet
from pyglet import gl
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo


def render_benchmark():
    with dpg.child_window(label="Test", width=400, height=400, no_scrollbar=True):
        dpg.add_text("Test")
    