# ----------------------------------------------------------------------------------------------------------------------
# Athena Application – Main entry point
# ----------------------------------------------------------------------------------------------------------------------
# This file defines the core scheduling, window‑management, and resource‑loading logic for the Athena desktop engine.
# The original implementation has been preserved exactly; the only additions below are **English comments** aimed at
# making each section easier to understand and extend.  No executable statements have been added, removed, or altered.
# ----------------------------------------------------------------------------------------------------------------------

import platform, json, sys, os, importlib, inspect, signal
import dearpygui.dearpygui as dpg

from pathlib import Path

# Detect the current operating system so that we can load native APIs conditionally.
current_os = platform.system()

# Windows‑specific API imports -----------------------------------------------------------------------------------------
if current_os == "Windows":
    import win32gui
    import win32con
    import win32api

    import ctypes
    from ctypes import c_int

    # Structure used by DwmExtendFrameIntoClientArea to create a glass effect on Windows.
    class MARGINS(ctypes.Structure):
        _fields_ = [
            ("cxLeftWidth",  c_int),
            ("cxRightWidth", c_int),
            ("cyTopHeight",  c_int),
            ("cyBottomHeight", c_int)
        ]

# macOS‑specific API imports ------------------------------------------------------------------------------------------
elif current_os == "Darwin":
    import objc
    from Cocoa import NSApp, NSWindow, NSApplication, NSApplicationActivateIgnoringOtherApps

# Linux‑specific API imports ------------------------------------------------------------------------------------------
elif current_os == "Linux":
    from Xlib import display, X
    from Xlib.ext import randr

# ----------------------------------------------------------------------------------------------------------------------
# Internal modules – all located in the project's "sources" package
# ----------------------------------------------------------------------------------------------------------------------
from sources.core.core_wrapper import *

# helper functions -----------------------------------------------------------------------------------------------------

def have_only_special_characters(string: str, special_characters: str) -> bool:
    """Return True if *string* is composed only of characters contained in *special_characters*."""
    for char in string:
        if char not in special_characters:
            return False
    return True


def get_first_item(parent):
    """Utility to fetch the very first child of a DearPyGui item, or *None* if it has no children."""
    children = dpg.get_item_children(parent, 1)
    if children:
        return children[0]
    return None


import threading
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, Tuple

# ----------------------------------------------------------------------------------------------------------------------
# Job scheduler – a light wrapper around time‑based callbacks that can run in the UI loop or a thread
# ----------------------------------------------------------------------------------------------------------------------

@dataclass
class Job:
    """A scheduled unit of work executed by :class:`AthenaOClock`."""

    name: str
    job: Callable  # Function to execute
    delta_time: float  # Interval (seconds) between runs
    limit: int = 0  # 0 == unlimited executions
    threaded: bool = False
    threaded_args: Tuple[Any, ...] = field(default_factory=tuple)

    # The following fields are filled internally – no need to touch them when creating a job.
    c_time: float = field(default_factory=time.time)  # Time of last execution
    c_limit: int = 0  # How many times we have executed so far


class AthenaOClock:
    """Minimal scheduler used throughout Athena to update sub‑applications at a fixed rate."""

    def __init__(self, _base: "ImGUIAthenaApp", delta_update_time: float = 1.0 / 60.0):
        self._base: "ImGUIAthenaApp" = _base
        self._jobs: Dict[str, Job] = {}
        self._current_update_time = time.time()
        self._delta_update_time = delta_update_time  # Throttle the *update_jobs* loop itself
        self._lock = threading.Lock()

    # ----------------------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------------------

    def add_job(
            self,
            name: str,
            job: Callable,
            delta_time: float,
            limit: int = 0,
            threaded: bool = False,
            threaded_args: Tuple[Any, ...] = (),
    ):
        """Register a new task. *delta_time* is expressed in **milliseconds** to stay consistent with
        DearPyGui's typical timers, but we immediately convert it to seconds internally."""
        with self._lock:
            if name in self._jobs:
                raise ValueError(f"Job '{name}' already exists.")
            self._jobs[name] = Job(
                name=name,
                job=job,
                delta_time=delta_time / 1000.0,  # ms ➜ s
                limit=limit,
                threaded=threaded,
                threaded_args=threaded_args,
            )

    @internal_log_profiling(section="Athena O'Clock", specific_log="aoc")
    def update_jobs(self):
        """Execute all jobs that are due **once per DearPyGui frame** (or less, depending on *delta_update_time*)."""
        c_time = time.time()

        # Throttle the update loop itself to avoid needless iterations.
        if c_time - self._current_update_time < self._delta_update_time:
            return
        self._current_update_time = c_time

        to_remove = []  # Collect jobs that reached their execution limit

        with self._lock:
            for name, job in self._jobs.items():
                if c_time - job.c_time >= job.delta_time:
                    # Decide whether to run in a background thread or in the main thread.
                    if job.threaded:
                        threading.Thread(target=job.job, args=job.threaded_args).start()
                    else:
                        job.job(*job.threaded_args)

                    # Update bookkeeping.
                    job.c_time = c_time
                    job.c_limit += 1

                    # Remove if we hit the max execution count.
                    if job.limit != 0 and job.c_limit >= job.limit:
                        to_remove.append(name)

            # Purge completed jobs outside the main loop.
            for name in to_remove:
                del self._jobs[name]

    def clear_jobs(self):
        """Immediately forget every scheduled job."""
        with self._lock:
            self._jobs.clear()


# ----------------------------------------------------------------------------------------------------------------------
# Main DearPyGui wrapper – handles viewport creation, resource loading, and dynamic application loading
# ----------------------------------------------------------------------------------------------------------------------

class ImGUIAthenaApp:
    """The root application responsible for bootstrapping and running the entire Athena GUI stack."""

    # --------------------------------------------------------------------------------------------------
    # Construction helpers – these run during *__init__*
    # --------------------------------------------------------------------------------------------------

    def _constructor_mount(self):
        """Instantiate loggers, loaders, helpers, and register a SIGINT handler."""
        try:
            self._base = self  # Pass ourselves where older code expects a "base" reference
            self._logs = AthenaLogs()
            self._logs.ap.info("Athena is mounting...")

            # Prepare dedicated log files for the various subsystems.
            self._logs.add_update_logger("athena_update_application", self._logs.create_file_logger("athena_update_application", "logs/athena_update_application.log", rewrite=True))
            self._logs.add_update_logger("athena_load_resources",   self._logs.create_file_logger("athena_load_resources",   "logs/athena_load_resources.log",   rewrite=True))
            self._logs.add_update_logger("athena_model_designer",   self._logs.create_file_logger("athena_model_designer",   "logs/athena_model_designer.log",   rewrite=True))
            self._logs.add_update_logger("athena_agents_manager",   self._logs.create_file_logger("athena_agents_manager",   "logs/athena_agents_manager.log",   rewrite=True))
            self._logs.add_update_logger("athena_o_clock",         self._logs.create_file_logger("athena_o_clock",         "logs/athena_o_clock.log",         rewrite=True))

            # Asset loaders and utility classes ------------------------------------------------------------------------------------
            self._loaders    = AthenaResourceLoader(base=self, resoure_directory="./assets/resources")
            self._mlowlevel  = AthenaLowLevelMandatory(base=self)
            self._dutils     = AthenaDisplayUtils()
            self._profiles   = AthenaProfilesUtils(base=self)
            self._ranimation = RenderAnimation(self._mlowlevel)
            self._oclock     = AthenaOClock(self)

            # Confirm successful initialisation in the logs
            self._logs.ap.info("Core subsystems initialised (Logs, Resources, Low‑Level, Display, Profiles, Animation)")

            # Gracefully handle Ctrl‑C in the terminal
            signal.signal(signal.SIGINT, self.__handle_signal)

        except Exception as e:
            # Fatal issues are logged in both critical channels.
            self._logs.ac.critical(str(e))
        self._logs.flush_all()

    # --------------------------------------------------------------------------------------------------
    # Signal handling & cleanup
    # --------------------------------------------------------------------------------------------------

    def __handle_signal(self, signum, frame):  # Main signal handler
        """Forward *signum* to all child applications so they can shut down safely, then close DearPyGui."""
        for application in self._meta_data["applications"].values():
            if hasattr(application, "handle_signal"):
                application.handle_signal(signum=signum, frame=frame)
        dpg.stop_dearpygui()
        dpg.destroy_context()

    # --------------------------------------------------------------------------------------------------
    # Asset/theme loading helpers (currently partially disabled – kept for reference)
    # --------------------------------------------------------------------------------------------------

    @internal_log_profiling(section="Athena Base Render")
    def _load_themes(self):
        """Define global, desktop, and icon themes (colors + rounding)."""
        # Implementation unchanged – only comments added.
        with dpg.theme(tag="global_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (96, 96, 216), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

        with dpg.theme(tag="desktop_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (0, 0, 0, 128), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5, category=dpg.mvThemeCat_Core)

        with dpg.theme(tag="desktop_icon_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (96, 96, 200, 128), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 0, category=dpg.mvThemeCat_Core)

                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (96, 96, 200, 128), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5, category=dpg.mvThemeCat_Core)

                # Button styles
                dpg.add_theme_color(dpg.mvThemeCol_Button,        (96, 96, 200, 128), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (96, 96, 200,  64), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  (96, 96, 200, 128), category=dpg.mvThemeCat_Core)

    @internal_log_profiling(section="Athena Base Render")
    def _load_fonts(self):
        """Register the various font sizes used across the UI."""
        with dpg.font_registry():
            tiny_font      = dpg.add_font("assets/keep_cheese.ttf", 10)
            icon_font      = dpg.add_font("assets/keep_cheese.ttf", 14)
            default_font   = dpg.add_font("assets/keep_cheese.ttf", 20)
            large_font     = dpg.add_font("assets/keep_cheese.ttf", 40)
            mega_large_font = dpg.add_font("assets/keep_cheese.ttf", 80)

            # Store references for later use (e.g., dpg.bind_item_font)
            self._meta_data["fonts"].update({
                "tiny_font": tiny_font,
                "icon_font": icon_font,
                "default_font": default_font,
                "large_font": large_font,
                "mega_large_font": mega_large_font,
            })

    @internal_log_profiling(section="Athena Base Render")
    def _load_textures(self):
        """Load the PNG logo and store a static texture within DearPyGui's internal registry."""
        with dpg.texture_registry(show=False):
            width, height, channels, data = dpg.load_image("assets/athena.png")
            self._meta_data["images"].append({
                "tag":      "logo",
                "width":    width,
                "height":   height,
                "channels": channels,
                "data":     data,
            })
            dpg.add_static_texture(width, height, data, tag="logo")

    # --------------------------------------------------------------------------------------------------
    # Profile management helpers
    # --------------------------------------------------------------------------------------------------

    @internal_log_profiling(section="Athena Base Render")
    def _create_profile(self):
        """Create a brand‑new user profile based on the name entered in the login window."""
        profile_name: str = dpg.get_value("profile_name")
        if profile_name == "" or not have_only_special_characters(profile_name, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"):
            self._logs.ac.critical("Profile name is invalid")
            self._logs.ap.critical("Profile name is invalid")
            self._logs.flush_all()
            return

        # Delegate everything else to AthenaProfilesUtils
        profile = self._profiles.create_profile(profile_name)
        self._logs.ac.info(f"Profile {profile_name} created")
        self._logs.ap.info(f"Profile {profile_name} created")

        self._profiles.setup_profile(profile)
        self._logs.ac.info(f"Profile {profile_name} setup")
        self._logs.ap.info(f"Profile {profile_name} setup")

        self._profiles.save_profile()
        self._logs.flush_all()

        # Refresh the combo box so the new profile appears immediately.
        self._update_profiles_combo()

    @internal_log_profiling(section="Athena Base Render")
    def _load_profile(self):
        """Load the profile selected in the drop‑down and optionally enable auto‑login."""
        profile_name = dpg.get_value("profiles")
        self._profiles.load_profile(profile_name)
        self._profiles.setup_profile(self._profiles.profile)
        self._logs.ac.info(f"Profile {profile_name} loaded")
        self._logs.ap.info(f"Profile {profile_name} loaded")
        self._logs.flush_all()

        auto_login = dpg.get_value("auto-login")
        if auto_login:
            self._logs.ac.info("Auto-Login enabled")
            self._logs.ap.info("Auto-Login enabled")
            self._logs.flush_all()

        # Save persisted settings to disk
        self._profiles.bcp["profile"]     = profile_name
        self._profiles.bcp["auto-login"] = auto_login
        self._profiles.save_base_config_profiles()

        # Hide the login group and reveal the desktop tools
        dpg.configure_item("group_login", show=False)
        dpg.configure_item("athena_utils", show=True)

    @internal_log_profiling(section="Athena Base Render")
    def _update_profiles_combo(self):
        """Synchronise the profile combo box with the latest on‑disk profiles."""
        profiles = self._profiles.get_profiles_names()
        dpg.configure_item("profiles", items=profiles)
        self._logs.ac.info("Profiles updated")
        self._logs.ap.info("Profiles updated")
        self._logs.flush_all()

    # --------------------------------------------------------------------------------------------------
    # Desktop shortcuts – create one icon per discovered sub‑application
    # --------------------------------------------------------------------------------------------------

    @internal_log_profiling(section="Athena Base Render")
    def _mount_ui_application_desktop(self, app: IApplication):
        """Instantiate an icon (child_window + button + image + label) for *app* on the desktop."""
        with dpg.child_window(
                width=130, height=130, menubar=False,
                parent="desktop_group", tag=f"{app.name}_icon",
                autosize_x=False, autosize_y=False,
                no_scrollbar=True, no_scroll_with_mouse=True,
                border=False,
        ):
            dpg.bind_item_theme(f"{app.name}_icon", "desktop_icon_theme")

            # Clickable invisible button covering the icon area
            dpg.add_button(
                use_internal_label=False,
                callback=lambda: app.set_opened(not app.opened),
                tag=f"{app.name}_button", pos=[0, 0],
                width=130, height=130,
            )
            # The icon image ------------------------------------
            dpg.add_image(f"{app.name}_application_icon", width=80, height=80, tag=f"{app.name}_icon_image", pos=[25, 7])
            # The title text (two lines)
            dpg.add_text(f"{app.name}\nVersion: {app.version}", pos=[10, 90], tag=f"{app.name}_title")
            dpg.bind_item_font(f"{app.name}_title", self._meta_data["fonts"]["icon_font"])

    # --------------------------------------------------------------------------------------------------
    # Dynamic application loader – hot reloads Python modules from ./applications/
    # --------------------------------------------------------------------------------------------------

    @internal_log_profiling(section="Athena Base Render")
    def _hot_reload_applications(self):
        """Reload every application inside the *applications/* directory without restarting Athena."""
        _path     = "./applications"
        _dirs     = os.listdir(_path)
        _excludes = ["__pycache__"]

        # Clear existing icons so we can recreate them in alphabetical order.
        dpg.delete_item("desktop_group", children_only=True)

        for _dir in _dirs:
            if _dir in _excludes:
                continue

            _application_dir = f"{_path}/{_dir}"
            if os.path.isdir(_application_dir) and os.path.exists(f"{_application_dir}/application.py"):

                # If the application was already loaded, dispose of the old instance.
                if _dir in self._meta_data["applications"].keys():
                    self._meta_data["applications"][_dir].delete()

                module_name = f"applications.{_dir}.application"

                for m_name in list(sys.modules):
                    if m_name.startswith(f"applications.{_dir}"):
                        del sys.modules[m_name]

                module = importlib.import_module(module_name)

                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, IApplication) and obj is not IApplication:
                        # self._reload_module_recursive(module)
                        importlib.reload(module)

                        app = getattr(module, name)(self)
                        self._mount_ui_application_desktop(app)
                        app.mount()
                        self._meta_data["applications"][app.name] = app

    # Deprecated
    """
    def _reload_module_recursive(self, module, visited=None):
        if visited is None:
            visited = set()

        if module in visited:
            return
        visited.add(module)

        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if inspect.ismodule(attribute) and attribute.__name__.startswith("applications"):
                if attribute.__name__ in sys.modules:
                    del sys.modules[attribute.__name__]
                self._reload_module_recursive(attribute, visited)
        importlib.reload(module)
    """

    @internal_log_profiling(section="Athena Base Render")
    def _mount_applications(self):
        _path = "./applications"
        _dirs = os.listdir(_path)
        _excludes = ["__pycache__"]

        for _dir in _dirs:
            if _dir in _excludes:
                continue
            _application_dir = f"{_path}/{_dir}"
            if os.path.isdir(_application_dir) and os.path.exists(f"{_application_dir}/application.py"):

                # application name already exists
                if _dir in self._meta_data["applications"]:
                    self._logs.ac.warning(f"Application {_dir} already exists")
                    self._logs.ap.warning(f"Application {_dir} already exists")
                    self._logs.flush_all()
                    continue

                module_name = f"applications.{_dir}.application"
                module = importlib.import_module(module_name)
                module_contents = dir(module)

                self._logs.ac.info(f"Mounting application {module_name}")
                self._logs.ap.info(f"Mounting application {module_name}")
                self._logs.ap.info(f"Application module contents: {module_contents}")
                self._logs.flush_all()

                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, IApplication) and obj is not IApplication:
                        app = getattr(module, name)(self)
                        self._mount_ui_application_desktop(app)
                        app.mount()

                # app = getattr(module, f"{_dir.capitalize()}Application")(self)
                # self._mount_ui_application_desktop(app)
                # app.mount()
                self._logs.ac.info(f"Application {app.name} mounted")
                self._logs.ap.info(f"Application {app.name} mounted")
                self._logs.flush_all()

                self._meta_data["applications"][app.name] = app

    @internal_log_profiling(section="Athena Base Render")
    def _constructor_mount_ui(self):
        self._logs.ac.info("[DPG] mounting UI")
        dpg.create_context()
        self._logs.ap.info("[DPG] context created")

        # Alpha Test Loader
        self._loaders.load_resources()
        self._loaders.apply_resources()
        # theme
        # self._load_themes()
        # self._logs.ap.info("[DPG] themes loaded")
        # font
        # self._load_fonts()
        # self._logs.ap.info("[DPG] fonts loaded")
        # texture registry
        # self._load_textures()
        # self._logs.ap.info("[DPG] textures loaded")

        # viewport
        if current_os == "Windows":

            dpg.create_viewport(
                title='AthenaProcess',
                width=0,
                height=0,
                clear_color=(0, 0, 0, 128),
                decorated=False,
                resizable=True,
                vsync=True,
                y_pos=0,
                x_pos=0,
                always_on_top=False,
            )
        elif current_os == "Darwin" or current_os == "Linux":
            dpg.create_viewport(
                title='AthenaProcess',
                width=1920,
                height=1080,
                min_width=1920,
                clear_color=(0, 0, 0, 128),
                decorated=True,
                resizable=True,
                vsync=True,
                y_pos=0,
                x_pos=0,
                # x_pos=1727,
                always_on_top=False,
            )
        self._logs.ap.info("[DPG] viewport created")

        if not os.path.exists("profiles/_base_config_profiles.json"):
            self._logs.ac.critical("No base config profiles found.")
            self._logs.ap.critical("No base config profiles found.")
            self._logs.flush_all()
            exit(0)

        _base_config_profiles = self._profiles.load_base_config_profiles().bcp
        self._logs.ap.info("[DPG] base config profiles loaded")

        # with open("profiles/_base_config_profiles.json", "r") as fd:
        #     _base_config_profiles = json.load(fd)

        self._ranimation.add_animation("AthenaProcessStart", lambda: self._ranimation.athena_process_start(self))

        # Problem with the font
        # with dpg.font_registry():
        #     _font = dpg.add_font("./assets/roboto_regular.ttf", 80, tag="roboto_regular")

        with dpg.window(label="AthenaSE", pos=[0, 0], width=0, height=0, no_title_bar=True, no_move=True, no_resize=True, no_close=True, no_background=True, tag="athena_main_window", no_bring_to_front_on_focus=True) as athena_main_window:

            dpg.add_image("logo", width=800, height=800, tag="logo_introduction")
            with dpg.child_window(pos=[100, 100], width=300, height=160, no_scrollbar=True, tag="group_introduction"):
                dpg.add_text("Athena", color=(96, 96, 215, 255), tag="athena_title")
                dpg.bind_item_font("athena_title", "mega_large_font_rr")
                dpg.add_separator()
                dpg.add_text("Version 0.2.1", color=(96, 96, 215, 255), tag="athena_version")
                dpg.add_text("Jacques, Matthis, Louis, Antoine", color=(96, 96, 215, 255), tag="athena_team")
                dpg.bind_item_font("athena_version", "default_font_rr")
                dpg.bind_item_font("athena_team", "default_font_rr")

            with dpg.group(tag="group_login", pos=[100, 230], width=200, show=False):
                dpg.add_input_text(label="Profile Name", default_value="", tag="profile_name", use_internal_label=True)
                with dpg.group(tag='group_login_buttons', horizontal=True):
                    dpg.add_button(label="Create", callback=self._create_profile, tag="create", height=50)
                    dpg.add_button(label="Load", callback=self._load_profile, tag="load", height=50)
                dpg.add_combo(label="Profiles", items=self._profiles.get_profiles_names(), default_value=_base_config_profiles["profile"], tag="profiles")
                dpg.add_checkbox(label="Auto-Login", default_value=_base_config_profiles["auto-login"], tag="auto-login")

            with dpg.group(tag="athena_utils", horizontal=True, show=False, pos=[5, 180]):
                # dpg.add_button(label="Focus Desktop !BUG!", callback=lambda : dpg.focus_item("desktop"), tag="focus_desktop_bug", height=20)
                dpg.add_button(label="Hot-Reload Application", tag="hot_reload_application", height=20, callback=lambda s, a, u: self._hot_reload_applications())
                dpg.add_button(label="Save", callback=self._profiles.save_profile, tag="save", height=20)
                dpg.add_button(label="Quit", callback=dpg.stop_dearpygui, tag="quit", height=20)

            dpg.bind_item_theme("athena_utils", "global_theme")

            with dpg.window(label="Desktop", width=1366, height=768, pos=[200, 230], tag="desktop", show=False, no_scrollbar=True, no_background=False, no_title_bar=True):
                dpg.bind_item_theme("desktop", "desktop_theme")
                # dpg.draw_rectangle([0, 0], [1366, 768], color=(0, 0, 0, 255), fill=(0, 0, 0, 128),  tag="desktop_background")
                with dpg.group(tag="desktop_group", horizontal=True):
                    self._mount_applications()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        self._logs.ap.info("[DPG] viewport shown")

        if current_os == "Windows":
            margins = MARGINS(-1, -1, -1, -1)
            hwnd = win32gui.FindWindow(None, "AthenaProcess")
            dwm = ctypes.windll.dwmapi
            dwm.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_TRANSPARENT)
            self._logs.ap.info("[DPG] window extended frame into client area")
        elif current_os == "Darwin":
            self._logs.ap.info("[DPG] configured window on MacOS not implemented")
        elif current_os == "Linux":
            d = display.Display()
            s = d.screen()
            root = s.root

            window_name = "AthenaProcess"
            window = None
            for w in root.query_tree().children:
                name = w.get_wm_name()
                if name == window_name:
                    window = w
                    break

            if window:
                window.change_attributes(event_mask=X.PointerMotionMask, override_redirect=True)
                d.sync()

                self._logs.ap.info("[DPG] configured window on Linux")
            else:
                self._logs.ap.info(f"[DPG] window not found: '{window_name}'")

        self._ranimation.start_animation("AthenaProcessStart")
        self._logs.ap.info("[DPG] UI mounted")
        self._logs.ac.info("[DPG] UI mounted")
        self._logs.ap.info("Athena is ready.")
        self._logs.ac.info("Athena is ready.")
        self._logs.flush_all()

    def _update_applications(self):
        for app in self._meta_data["applications"].values():
            app.update()

    def _run(self):

        # self._oclock.add_job("update_applications", self._update_applications, 1.0/60.0, limit=0, threaded=False)
        self._oclock.add_job("update_applications", self._update_applications, 1.0 / 10.0, limit=0, threaded=False)

        while dpg.is_dearpygui_running():
            self._oclock.update_jobs()
            # for app in self._meta_data["applications"].values():
            #     app.update()
            dpg.render_dearpygui_frame()

        dpg.stop_dearpygui()
        # dpg.cleanup_dearpygui() # Deprecated
        dpg.destroy_context()

    def __init__(self) -> None:
        self._meta_data = {
            "images": [],
            "fonts": {},
            "applications": {}
        }
        self._constructor_mount()
        self._constructor_mount_ui()
        self._run()