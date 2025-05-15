import platform

current_os = platform.system()

import dearpygui.dearpygui as dpg
import threading



# from  sources.core.render.athena_base_render import ImGUIAthenaApp

class RenderAnimation:
    
    def __init__(self, mlowlevel) -> None:
        self._mlowlevel = mlowlevel
        
        self._animations_threads : dict = {}
    
    def add_animation(self, name: str, animation: callable) -> None:
        self._animations_threads[name] = threading.Thread(target=animation)
    
    def start_animation(self, name: str) -> None:
        assert name in self._animations_threads, f"Animation {name} not found"
        assert not self._animations_threads[name].is_alive(), f"Animation {name} is already running"
        self._animations_threads[name].start()
        
    def check_animation(self, name: str) -> bool:
        assert name in self._animations_threads, f"Animation {name} not found"
        return self._animations_threads[name].is_alive()
    
    
    # Animation
    
    def _athena_process_start(self, base: 'ImGUIAthenaApp') -> None:
        if current_os == "Windows":
            monitors = base._dutils.format_monitors_information(base._dutils.get_all_monitors())
        
            height = 0
            width = 0
        
            i, j = 0, 1
        
            for monitor in monitors:
                height = max(height, monitor["Coordinates"]["Bottom"] - monitor["Coordinates"]["Top"])
                width += monitor["Coordinates"]["Right"] - monitor["Coordinates"]["Left"]
        elif current_os == "Darwin":
            height = 1280
            width = 1440
            i, j = 0, 1
        elif current_os == "Linux":
            height = 1080
            width = 1920
            i, j = 0, 1
        
        logo_width = dpg.get_item_configuration("logo_introduction")["width"]
        logo_height = dpg.get_item_configuration("logo_introduction")["height"]
        
        logo_x = (width - logo_width) // 2
        logo_y = (height - logo_height) // 2
        
        _skip = True
        
        
        if not _skip:
            for _ in range(height):
                dpg.set_viewport_height(j)
                # dpg.configure_item("background_app", pmin=[0, 0], pmax=[i, j])
                dpg.configure_item("athena_main_window", width=i, height=j)
                
                logo_y = (j - logo_height) // 2
                dpg.configure_item("logo_introduction", pos=[logo_x, logo_y], width=logo_width, height=logo_height)
                j += 1
                base._mlowlevel.sleep(1)
            for _ in range(width):
                base_color = (96, 96, 215)
                percentage = i / width
                opacity = int(255 * percentage)
                color = (*base_color, opacity)
                
                dpg.set_viewport_width(i)
                # dpg.configure_item("background_app", pmin=[0, 0], pmax=[i, j])
                dpg.configure_item("athena_main_window", width=i, height=j)
                dpg.configure_item("athena_title", color=color)
                dpg.configure_item("athena_version", color=color)
                dpg.configure_item("athena_team", color=color)
            
                logo_x = (i - logo_width) // 2
                dpg.configure_item("logo_introduction", pos=[logo_x, logo_y], width=logo_width, height=logo_height)
                i += 1
                base._mlowlevel.sleep(1)
        else:
            dpg.set_viewport_height(height)
            dpg.set_viewport_width(width)
            dpg.configure_item("athena_main_window", width=width, height=height)
            dpg.configure_item("logo_introduction", pos=[logo_x, logo_y], width=logo_width, height=logo_height)
            dpg.configure_item("athena_title", color=(96, 96, 215, 255))
            dpg.configure_item("athena_version", color=(96, 96, 215, 255))
            dpg.configure_item("athena_team", color=(96, 96, 215, 255))
            
        dpg.configure_item("group_login", show=True)
        animation_translate_resize_a = (logo_x, logo_y, logo_width, logo_height)
        animation_translate_resize_a_target = (width - 130, 130, 120, 120)
        
        
        steps = 100
        step_x = (animation_translate_resize_a_target[0] - animation_translate_resize_a[0]) / steps
        step_y = (animation_translate_resize_a_target[1] - animation_translate_resize_a[1]) / steps
        step_width = (animation_translate_resize_a_target[2] - animation_translate_resize_a[2]) / steps
        step_height = (animation_translate_resize_a_target[3] - animation_translate_resize_a[3]) / steps
        
        for step in range(steps):
            logo_x += step_x
            logo_y += step_y
            logo_width += step_width
            logo_height += step_height
            
            dpg.configure_item("logo_introduction", pos=[logo_x, logo_y], width=int(logo_width), height=int(logo_height))
            base._mlowlevel.sleep(10)
        
        dpg.configure_item("group_introduction", pos=[5, 5])
        # dpg.configure_item("athena_title", pos=[20, 5])
        # dpg.configure_item("athena_version", pos=[20, 100])
        # dpg.configure_item("athena_team", pos=[20, 120])
        
        dpg.configure_item("desktop", show=True)
        
        
        if base._profiles.bcp["auto-login"]:
            try:
                base._profiles.load_profile(base._profiles.bcp["profile"])
                base._profiles.setup_profile(base._profiles.profile)
                base._logs.ac.info(f"Profile {base._profiles.profile['name']} loaded successfully")
                base._logs.ap.info(f"Profile {base._profiles.profile['name']} loaded successfully")
                base._logs.flush_all()

                dpg.configure_item("group_login", show=False)
                dpg.configure_item("athena_utils", show=True)
            except Exception as e:
                base._logs.ap.critical(str(e) + " [load_profile]")
                base._logs.ac.critical(str(e) + " [load_profile]")
                base._logs.flush_all()
        
    def athena_process_start(self, base) -> None:
        self._mlowlevel.do_task_period(lambda : self._athena_process_start(base), 1)