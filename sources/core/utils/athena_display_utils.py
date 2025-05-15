import platform

current_os = platform.system()

if current_os == "Windows":
    import win32gui
    import win32con
    import win32api
    
    import ctypes
    from ctypes import c_int
elif current_os == "Darwin":
    import objc
    from Cocoa import NSApp, NSWindow, NSApplication, NSApplicationActivateIgnoringOtherApps
elif current_os == "Linux":
    from Xlib import display, X
    from Xlib.ext import randr

class AthenaDisplayUtils:
    def __init__(self):
        self.monitors = []


    # def get_all_monitors(self):
    #     if current_os == "Windows":
    #         return self.get_all_monitors_windows()
    #     elif current_os == "Darwin":
    #         return self.get_all_monitors_macos()
    #     elif current_os == "Linux":
    #         return self.get_all_monitors_linux()
    #     else:
    #         print(f"Système d'exploitation non supporté : {self.current_os}")
    #         return []

    
    # def get_all_monitors_windows(self):
    #     monitors = win32api.EnumDisplayMonitors()
    #     return self.format_monitors_information_windows(monitors)

    # def format_monitors_information_windows(self, monitors):
    #     formatted_monitors = []
    #     for monitor in monitors:
    #         hMonitor, hdcMonitor, rect = monitor
    #         formatted_monitors.append({
    #             "Handle": hMonitor,
    #             "Device Context": hdcMonitor,
    #             "Coordinates": {
    #                 "Left": rect[0],
    #                 "Top": rect[1],
    #                 "Right": rect[2],
    #                 "Bottom": rect[3]
    #             }
    #         })
    #     return formatted_monitors

    # def get_all_monitors_macos(self):
    #     max_displays = 16
    #     active_displays = (ctypes.c_uint32 * max_displays)()
    #     display_count = ctypes.c_uint32()

    #     result = Quartz.CGGetActiveDisplayList(max_displays, active_displays, ctypes.byref(display_count))
    #     if result != 0:
    #         print("Erreur lors de l'énumération des moniteurs sur macOS")
    #         return []

    #     formatted_monitors = []
    #     for i in range(display_count.value):
    #         display_id = active_displays[i]
    #         bounds = CGDisplayBounds(display_id)
    #         formatted_monitors.append({
    #             "Display ID": display_id,
    #             "Coordinates": {
    #                 "Left": int(bounds.origin.x),
    #                 "Top": int(bounds.origin.y),
    #                 "Right": int(bounds.origin.x + bounds.size.width),
    #                 "Bottom": int(bounds.origin.y + bounds.size.height)
    #             }
    #         })
    #     return formatted_monitors

    # def get_all_monitors_linux(self):
    #     d = display.Display()
    #     root = d.screen().root
    #     resources = root.xrandr_get_screen_resources()._data

    #     formatted_monitors = []
    #     for output in resources['outputs']:
    #         output_info = root.xrandr_get_output_info(output, resources['config_timestamp'])._data
    #         if output_info['connection'] == 0:  # Connected
    #             for mode in output_info['modes']:
    #                 mode_info = root.xrandr_get_mode_info(output, mode)._data
    #                 formatted_monitors.append({
    #                     "Output": output,
    #                     "Width": mode_info['width'],
    #                     "Height": mode_info['height'],
    #                     "Refresh Rate": mode_info['dotClock']  # Approximation
    #                 })
    #     d.close()
    #     return formatted_monitors

    @staticmethod
    def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
        monitors = dwData
        monitors.append((hMonitor, hdcMonitor, (lprcMonitor.left, lprcMonitor.top, lprcMonitor.right, lprcMonitor.bottom)))
        return True

    def get_all_monitors(self):
        return win32api.EnumDisplayMonitors()

    @staticmethod
    def format_monitors_information(monitors):
        formatted_monitors = []
        for monitor in monitors:
            hMonitor, hdcMonitor, (left, top, right, bottom) = monitor
            formatted_monitors.append({
                "Handle": hMonitor,
                "Device Context": hdcMonitor,
                "Coordinates": {
                    "Left": left,
                    "Top": top,
                    "Right": right,
                    "Bottom": bottom
                }
            })
        return formatted_monitors
