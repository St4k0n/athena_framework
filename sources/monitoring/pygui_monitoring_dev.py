import pyglet
from pyglet import gl
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

import win32gui
import win32con
import win32api

import ctypes

from ctypes import c_int

app_states = {
    "Application 1": False,
    "Application 2": False,
    "Application 3": False,
}

class ImGUIAthenaMonitoringApp:
    pass

    """ TODO: Implement ImGUIAthenaMonitoringApp class 
    1: If you can create docker containers (IMGUI) to let us move the monitoring to a separate window: remove the top bar of the window (not the viewport) else keep it but make it transparent
    2: Implement the following viewport:
        - Title: Athena
        - Manage all the viewports because each viewports will be a new menu. (Environments, Monitors, Logs, etc)
        - If you could create a transparent window: add a button to minimize/close/resize the window & general process.
    3: Implement the following viewport menu:
        - Title: Environments
        - this is a viewport where you could find all the entities (agents, clusters, etc) in the athena environment in a tree view or list with search bar. choose the best.
        - if i click on an entity, it will open a new viewport with the entity details.
    4: Implement the following viewport menu:
        - Title: Monitors
        - this part allow us to enable/disable the monitoring of the entities in the environment. each monitors will have a specific viewport from the entity.
        - in the monitor we could find line charts, bar charts, histogram chart, imshow chart, candle-sticks etc etc.
    5: Implement the following viewport menu:
        - Title: Logs
        - this part allow us to see the logs of the entities in the environment. each logs will have a specific viewport from the entity.
        - in the logs we could find text logs, image logs, video logs, etc etc.
    EXTRA: Implement extra features:
        - Add icons for the main viewport Athena that must be cool and beautiful.
        - Use your brain GPT do something cool and beautiful. cause something you did big shit to be honest x) and i m lazy to make the base of this.
    """

def total_width_monitors():
    width = 0
    monitors = win32api.EnumDisplayMonitors()
    for monitor in monitors:
        monitor_info = win32api.GetMonitorInfo(monitor[0])
        width += monitor_info['Monitor'][2] - monitor_info['Monitor'][0]
    return width

def max_height_monitors():
    height = 0
    monitors = win32api.EnumDisplayMonitors()
    for monitor in monitors:
        monitor_info = win32api.GetMonitorInfo(monitor[0])
        height = max(height, monitor_info['Monitor'][3] - monitor_info['Monitor'][1])
    return height


def get_screen_info():
    monitors = win32api.EnumDisplayMonitors()
    for monitor in monitors:
        monitor_info = win32api.GetMonitorInfo(monitor[0])
        print(f"Monitor: {monitor_info['Device']}")
        print(f"Width: {monitor_info['Monitor'][2] - monitor_info['Monitor'][0]}")
        print(f"Height: {monitor_info['Monitor'][3] - monitor_info['Monitor'][1]}")
        print(f"X: {monitor_info['Monitor'][0]}")
        print(f"Y: {monitor_info['Monitor'][1]}")

def child_window_callback(sender, app_name):
    if not app_states[app_name]:
        app_states[app_name] = True
        dpg.set_value(sender, "Loading...")
        dpg.configure_item(sender, color=(0, 255, 0, 255))

        dpg.set_item_callback(sender, lambda: print(f"{app_name} is running"))

        dpg.configure_item(sender, callback=lambda s: dpg.set_value(sender, app_name))

def create_test_3():
    
    
    get_screen_info()
    dpg.create_context()

    with dpg.theme() as custom_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (48, 48, 215, 128))  # RGBA color

    dpg.create_viewport(
        title='DearPyGui Transparent Window',
        width=total_width_monitors(),
        height=max_height_monitors(),
        clear_color=(0, 0, 0, 0),
        decorated=False,
        resizable=True,
        vsync=True,
        y_pos=0,
        x_pos=0,
        always_on_top=False,
    )
    
    with dpg.texture_registry(show=False):
        width, height, channels, data = dpg.load_image("assets/athena.png")
        dpg.add_static_texture(width, height, data, tag="icon1")

    with dpg.window(label="AthenaSE", no_title_bar=True, no_move=False, no_resize=True, no_close=True, no_background=True):
        dpg.draw_rectangle([0, 0], [total_width_monitors(), max_height_monitors()], color=(0, 0, 0, 128), fill=(0, 0, 0, 128))
        app_containers = [
            {"label": "Application 1", "pos": (50, 50)},
            {"label": "Application 2", "pos": (300, 50)},
            {"label": "Application 3", "pos": (550, 50)},
        ]
        
        for app in app_containers:
            with dpg.child_window(label=app["label"], width=120, height=120, pos=app["pos"], no_scrollbar=True) as child:
                dpg.add_image("icon1", width=100, height=100, pos=[0, 0])  # Centered image with specified size
                dpg.add_text(app["label"], tag=f"{child}_text")  # Bottom center text
                dpg.add_button(label="", width=120, height=120, callback=lambda s, a=app["label"]: child_window_callback(s, a))
                dpg.bind_item_theme(child, custom_theme)  # Appliquer le thème à chaque fenêtre enfant

            
    dpg.set_viewport_clear_color((0, 0, 0, 0))
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Windows API calls to extend the frame into the client area for transparency
    class MARGINS(ctypes.Structure):
        _fields_ = [("cxLeftWidth", c_int),
                    ("cxRightWidth", c_int),
                    ("cyTopHeight", c_int),
                    ("cyBottomHeight", c_int)]

    margins = MARGINS(-1, -1, -1, -1)
    hwnd = win32gui.FindWindow(None, "DearPyGui Transparent Window")
    dwm = ctypes.windll.dwmapi
    dwm.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

    # Optional: Make the window click-through
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_TRANSPARENT)

    # Main rendering loop
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


def create_test_2():
    # Créer une fenêtre pyglet avec transparence
    config = gl.Config(alpha_size=8)
    window = pyglet.window.Window(width=800, height=600, style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS, config=config)

    # Activer la transparence
    gl.glClearColor(0, 0, 0, 0)
    window.set_location(100, 100)

    # Récupérer le handle de la fenêtre pour définir la transparence
    hwnd = window._hwnd

    # Définir la transparence de la fenêtre en utilisant les API Windows
    extended_style_settings = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style_settings | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 128, win32con.LWA_ALPHA)  # 128 pour 50% de transparence

    # Fonction de mise à jour pour DearPyGui dans la boucle pyglet
    def update(dt):
        dpg.render_dearpygui_frame()

    # Initialiser DearPyGui
    dpg.create_context()

    # Créer la fenêtre principale de DearPyGui
    with dpg.window(label="Main Window", width=600, height=400, no_title_bar=True, no_resize=True) as main_window:
        dpg.add_text("Hello, this is a transparent window!")
        dpg.add_button(label="Click Me")

    # Configurer la fenêtre principale
    dpg.set_primary_window(main_window, True)

    # Configurer le viewport
    dpg.create_viewport(title='Transparent Window', width=800, height=600, clear_color=[0, 0, 0, 0])
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Planifier la mise à jour de DearPyGui
    pyglet.clock.schedule_interval(update, 1/60)

    # Démarrer la boucle pyglet
    @window.event
    def on_draw():
        window.clear()

    pyglet.app.run()

    # Détruire le contexte DearPyGui après fermeture de la fenêtre
    dpg.destroy_context()

    
def create_test():
    # Initialiser DearPyGui
    dpg.create_context()
    
    # Créer la fenêtre principale
    with dpg.window(label="Main Window", pos=(100, 100), width=600, height=400, no_title_bar=True, no_resize=True) as main_window:
        dpg.add_text("Hello, this is a transparent window!")
        dpg.add_button(label="Click Me")

    # Configurer la fenêtre principale pour qu'elle soit transparente
    #dpg.set_primary_window(main_window, True)
    #dpg.set_viewport_clear_color([0, 0, 0, 0])  # RGBA, dernière valeur est l'opacité (0 = transparent)

    # Créer la fenêtre et le contexte
    dpg.create_viewport(title='Transparent Window', width=800, height=600, clear_color=[0, 0, 0, 0])
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Démarrer l'interface
    dpg.start_dearpygui()
    dpg.destroy_context()

class ImGUIAthenaMonitoringApp:
    def __init__(self):
        dpg.create_context()
        self.setup_viewport()
        self.setup_main_menu()
        self.setup_environment_menu()
        self.setup_monitors_menu()
        self.setup_logs_menu()
        dpg.create_viewport(title='Athena', width=1200, height=800, clear_color=(0, 0, 0, 0))
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

    def setup_viewport(self):
        with dpg.viewport_menu_bar():
            dpg.add_menu_item(label="Environments", callback=self.show_environment_menu)
            dpg.add_menu_item(label="Monitors", callback=self.show_monitors_menu)
            dpg.add_menu_item(label="Logs", callback=self.show_logs_menu)

    def setup_main_menu(self):
        with dpg.window(label="Athena Main Menu", tag="MainMenu", width=800, height=600):
            dpg.add_text("Welcome to Athena Monitoring System")

    def setup_environment_menu(self):
        with dpg.window(label="Environments", tag="EnvironmentsMenu", width=800, height=600, show=False):
            dpg.add_text("List of Entities in Athena Environment")
            dpg.add_input_text(label="Search Entities", callback=self.search_entities)
            with dpg.child_window(autosize_x=True, autosize_y=True):
                with dpg.tree_node(label="Cluster 1"):
                    dpg.add_button(label="Agent 1", callback=lambda: self.show_entity_details("Agent 1"))
                    dpg.add_button(label="Agent 2", callback=lambda: self.show_entity_details("Agent 2"))
                with dpg.tree_node(label="Cluster 2"):
                    dpg.add_button(label="Agent 3", callback=lambda: self.show_entity_details("Agent 3"))
                    dpg.add_button(label="Agent 4", callback=lambda: self.show_entity_details("Agent 4"))

    def setup_monitors_menu(self):
        with dpg.window(label="Monitors", tag="MonitorsMenu", width=800, height=600, show=False):
            dpg.add_text("Monitor the Entities")
            dpg.add_button(label="Enable Monitoring", callback=self.enable_monitoring)
            dpg.add_button(label="Disable Monitoring", callback=self.disable_monitoring)

    def setup_logs_menu(self):
        with dpg.window(label="Logs", tag="LogsMenu", width=800, height=600, show=False):
            dpg.add_text("Logs of the Entities")
            with dpg.child_window(autosize_x=True, autosize_y=True):
                dpg.add_text("Log 1: Entity 1 started")
                dpg.add_text("Log 2: Entity 2 failed")
                dpg.add_text("Log 3: Entity 3 completed")

    def show_environment_menu(self):
        dpg.show_item("EnvironmentsMenu")
        dpg.hide_item("MainMenu")

    def show_monitors_menu(self):
        dpg.show_item("MonitorsMenu")
        dpg.hide_item("MainMenu")

    def show_logs_menu(self):
        dpg.show_item("LogsMenu")
        dpg.hide_item("MainMenu")

    def search_entities(self, sender, app_data):
        # Implement search functionality for entities
        print(f"Searching for: {app_data}")

    def show_entity_details(self, entity_name):
        # Create a new viewport for entity details
        with dpg.window(label=f"Details of {entity_name}", width=600, height=400):
            dpg.add_text(f"Details for {entity_name}")

    def enable_monitoring(self):
        print("Monitoring Enabled")

    def disable_monitoring(self):
        print("Monitoring Disabled")


def create_demo():
    dpg.create_context()
    dpg.create_viewport(title='Custom Title', width=600, height=600)


    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


import threading
import time
import ctypes


def animation_thread():
    timeBeginPeriod = ctypes.windll.winmm.timeBeginPeriod
    timeEndPeriod = ctypes.windll.winmm.timeEndPeriod
    Sleep = ctypes.windll.kernel32.Sleep
    i, j = 0, 0
    
    timeBeginPeriod(1)  # set resolution to 1 ms
    try:
        for _ in range(600):
            dpg.set_viewport_height(j)
            dpg.configure_item("Main Window", width=i, height=j)
            j += 1
            Sleep(1)
        for _ in range(600):
            dpg.set_viewport_width(i)
            dpg.configure_item("Main Window", width=i, height=j)
            i += 1
            Sleep(1)
    finally:
        timeEndPeriod(1)

def create_demo():
    dpg.create_context()
    dpg.create_viewport(title='Custom Title', width=800, height=800)


    # with dpg.window(label="Main Window", width=500, height=500, tag="Main Window"):
        # dpg.add_text("Hello, this is a transparent window!")
        # dpg.add_button(label="Click Me")

    # thread = threading.Thread(target=animation_thread)
    # thread.start()
    demo.show_demo()
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()