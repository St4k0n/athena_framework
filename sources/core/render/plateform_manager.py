import platform
import ctypes
from ctypes import c_int as CInt # Renommé pour éviter conflit potentiel

# Forward declaration for type hinting if AthenaLogs is in a separate file later
# from sources.core.core_wrapper import AthenaLogs # Supposons que AthenaLogs est ici

class PlatformManager:
    """
    Manages platform-specific operations like library imports and window manipulation.
    """

    # Windows specific structure
    class MARGINS(ctypes.Structure):
        _fields_ = [("cxLeftWidth", CInt),
                    ("cxRightWidth", CInt),
                    ("cyTopHeight", CInt),
                    ("cyBottomHeight", CInt)]

    def __init__(self, logs: 'AthenaLogs'):
        self._logs = logs
        self.current_os = platform.system()
        self.win32gui = None
        self.win32con = None
        self.win32api = None
        self.ctypes_windll_dwmapi = None
        self.objc = None
        self.Cocoa = None
        self.Xlib_display = None
        self.Xlib_X = None
        self.Xlib_randr = None # Bien que non utilisé dans le code d'origine pour la manip de fenêtre

        self._import_platform_libraries()

    def _import_platform_libraries(self):
        if self.current_os == "Windows":
            try:
                import win32gui
                import win32con
                import win32api
                self.win32gui = win32gui
                self.win32con = win32con
                self.win32api = win32api
                self.ctypes_windll_dwmapi = ctypes.windll.dwmapi
                self._logs.ap.info("Windows specific libraries imported.")
            except ImportError as e:
                self._logs.ac.error(f"Failed to import Windows specific libraries: {e}")
        elif self.current_os == "Darwin":
            try:
                import objc
                from Cocoa import NSApp, NSWindow, NSApplication, NSApplicationActivateIgnoringOtherApps
                self.objc = objc
                self.Cocoa = {
                    "NSApp": NSApp, "NSWindow": NSWindow,
                    "NSApplication": NSApplication,
                    "NSApplicationActivateIgnoringOtherApps": NSApplicationActivateIgnoringOtherApps
                }
                self._logs.ap.info("macOS specific libraries imported.")
            except ImportError as e:
                self._logs.ac.error(f"Failed to import macOS specific libraries: {e}")
        elif self.current_os == "Linux":
            try:
                from Xlib import display, X
                from Xlib.ext import randr
                self.Xlib_display = display
                self.Xlib_X = X
                self.Xlib_randr = randr # Store for potential future use
                self._logs.ap.info("Linux specific libraries imported.")
            except ImportError as e:
                self._logs.ac.error(f"Failed to import Linux specific libraries: {e}")
        else:
            self._logs.ac.warning(f"Unsupported OS: {self.current_os}. No specific libraries loaded.")
        self._logs.flush_all()

    def get_os_name(self) -> str:
        return self.current_os

    def create_platform_viewport(self, dpg_module, title: str, width: int, height: int,
                                 clear_color: tuple, vsync: bool, always_on_top: bool,
                                 x_pos: int = 0, y_pos: int = 0, min_width: int = 0, min_height: int = 0):
        """
        Creates a DPG viewport with platform-specific decorations.
        """
        if self.current_os == "Windows":
            dpg_module.create_viewport(
                title=title,
                width=width if width else 0, # Windows original behavior was 0 for auto
                height=height if height else 0, # Windows original behavior was 0 for auto
                clear_color=clear_color,
                decorated=False, # Key difference for Windows
                resizable=True,
                vsync=vsync,
                y_pos=y_pos,
                x_pos=x_pos,
                always_on_top=always_on_top,
            )
            self._logs.ap.info(f"[DPG] Windows viewport created: '{title}' (undecorated).")
        elif self.current_os == "Darwin" or self.current_os == "Linux":
            # Original code used fixed large values for Darwin/Linux
            # Making it more flexible by using passed width/height or defaulting if not provided
            dpg_module.create_viewport(
                title=title,
                width=width if width else 1920,
                height=height if height else 1080,
                min_width=min_width if min_width else (width if width else 1920),
                min_height=min_height if min_height else (height if height else 1080),
                clear_color=clear_color,
                decorated=True, # Key difference for Darwin/Linux
                resizable=True,
                vsync=vsync,
                y_pos=y_pos,
                x_pos=x_pos,
                always_on_top=always_on_top,
            )
            self._logs.ap.info(f"[DPG] {self.current_os} viewport created: '{title}' (decorated).")
        else:
            # Fallback for unsupported OS
            dpg_module.create_viewport(
                title=title, width=width, height=height, clear_color=clear_color,
                decorated=True, resizable=True, vsync=vsync, y_pos=y_pos, x_pos=x_pos,
                always_on_top=always_on_top, min_width=min_width, min_height=min_height
            )
            self._logs.ap.warning(f"[DPG] Viewport for unsupported OS '{self.current_os}' created with default decoration.")
        self._logs.flush_all()


    def apply_platform_window_effects(self, window_title: str):
        """
        Applies platform-specific window effects like transparency or borderless style.
        Should be called after dpg.show_viewport().
        """
        if self.current_os == "Windows":
            if not all([self.win32gui, self.win32con, self.ctypes_windll_dwmapi]):
                self._logs.ac.error("Windows libraries not loaded. Cannot apply window effects.")
                self._logs.flush_all()
                return

            hwnd = self.win32gui.FindWindow(None, window_title)
            if not hwnd:
                self._logs.ac.error(f"Could not find window: {window_title}")
                self._logs.flush_all()
                return

            margins = self.MARGINS(-1, -1, -1, -1)
            try:
                self.ctypes_windll_dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
                ex_style = self.win32gui.GetWindowLong(hwnd, self.win32con.GWL_EXSTYLE)
                self.win32gui.SetWindowLong(hwnd, self.win32con.GWL_EXSTYLE, ex_style | self.win32con.WS_EX_TRANSPARENT)
                self._logs.ap.info("[DPG] Windows: Extended frame into client area and set transparent style.")
            except Exception as e:
                self._logs.ac.error(f"Error applying Windows specific window effects: {e}")

        elif self.current_os == "Darwin":
            # Basic implementation attempt for macOS, might need more complex ObjC calls
            # For true borderless/transparent, more Cocoa work is needed.
            # This is a simplified placeholder based on typical needs.
            if not self.Cocoa:
                self._logs.ac.error("macOS (Cocoa) libraries not loaded. Cannot apply window effects.")
                self._logs.flush_all()
                return
            try:
                # This is a very basic example, real transparency and borderless might need more:
                # e.g. window.setOpaque_(False)
                #      window.setBackgroundColor_(NSColor.clearColor())
                #      window.setStyleMask_(NSBorderlessWindowMask)
                # Finding the correct NSWindow object associated with DPG's viewport is crucial and non-trivial.
                # DPG might not expose the native window handle directly in a way that's easy to grab here.
                # For now, just logging.
                self._logs.ap.info("[DPG] macOS window effect configuration: Further implementation needed for transparency/borderless beyond DPG's 'decorated=False'.")
                # Example of how one might try to get the main window if DPG used a standard NSApplication
                # ns_app = self.Cocoa["NSApp"]
                # if ns_app and ns_app.mainWindow():
                #     main_window = ns_app.mainWindow()
                # main_window.setAlphaValue_(0.8) # Example: make window semi-transparent
                # main_window.setOpaque_(False)
                # main_window.setBackgroundColor_(self.Cocoa["NSColor"].clearColor())
                # self._logs.ap.info("[DPG] Attempted to configure macOS window (example).")
                # else:
                #     self._logs.ap.warning("[DPG] Could not get NSApp or main window for macOS effects.")

            except Exception as e:
                self._logs.ac.error(f"Error applying macOS specific window effects: {e}")


        elif self.current_os == "Linux":
            if not all([self.Xlib_display, self.Xlib_X]):
                self._logs.ac.error("Linux (Xlib) libraries not loaded. Cannot apply window effects.")
                self._logs.flush_all()
                return
            try:
                d = self.Xlib_display.Display()
                s = d.screen()
                root = s.root
                window_id = None

                # Find the window by title
                # This is a common way but can be unreliable if titles change or are not unique
                for w_child in root.query_tree().children:
                    try:
                        name = w_child.get_wm_name()
                        if name and window_title in name: # Check if DPG title matches
                            # Check _NET_WM_PID to be more sure it's our window
                            pid_atom = d.intern_atom('_NET_WM_PID')
                            pid_prop = w_child.get_property(pid_atom, self.Xlib_X.AnyPropertyType, 0, 1)
                            if pid_prop and pid_prop.value and pid_prop.value[0] == os.getpid():
                                window_id = w_child
                                break
                    except (self.Xlib_X.BadWindow, self.Xlib_X.BadAccess): # Handle cases where window might have been destroyed
                        continue

                if window_id:
                    # Making a window borderless and transparent with Xlib can be complex
                    # and depends on the window manager.
                    # 'override_redirect=True' makes it ignore the WM, good for overlays
                    # but can lose focus, input, decorations.
                    # For transparency, you usually need a compositing manager running.
                    # DPG's internal X11 backend might already handle some of this if 'decorated=False'
                    # is set, but if you want to force it:
                    # window_id.change_attributes(event_mask=self.Xlib_X.StructureNotifyMask, override_redirect=True) # Example

                    # Set _NET_WM_WINDOW_TYPE to DOCK or DIALOG if you want it unmanaged by WM in some ways
                    # For transparency, one might set the _NET_WM_WINDOW_OPACITY atom
                    # opacity_atom = d.intern_atom('_NET_WM_WINDOW_OPACITY')
                    # opacity_value = int(0.8 * 0xFFFFFFFF) # 80% opacity
                    # window_id.change_property(opacity_atom, self.Xlib_X.Cardinal, 32, [opacity_value])

                    d.sync()
                    self._logs.ap.info(f"[DPG] Linux: Window '{window_title}' found. Further effects (like transparency) require compositor and specific X atom manipulation.")
                else:
                    self._logs.ap.warning(f"[DPG] Linux: Window '{window_title}' not found for applying effects.")
            except Exception as e:
                self._logs.ac.error(f"Error applying Linux specific window effects: {e}")
        else:
            self._logs.ap.info(f"No specific window effects to apply for OS: {self.current_os}")
        self._logs.flush_all()