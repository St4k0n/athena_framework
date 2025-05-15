from sources.core.decorators.athena_intern_lp import internal_log_profiling
from sources.core.utils.athena_colors import BLUE, RESET

from applications.iapplication import IApplication
import dearpygui.dearpygui as dpg


# {name_dir}Application
class TestApplication(IApplication):
    
    def __init__(self, base: "ImGUIAthenaApp") -> None:
        super().__init__(base=base, name="test", version="0.0.1", opened=False)

    @internal_log_profiling(section=f"{BLUE}Test Application{RESET}", specific_log="aua")
    def update(self):
        pass
        
    @internal_log_profiling(section="Test Application")
    def mount(self):
        with dpg.window(
            label=self.name, 
            tag=f"{self.name}_application_window",
            width=500, 
            height=500, 
            no_title_bar=False, 
            no_move=False,
            no_resize=True,
            no_collapse=True, 
            no_close=False, 
            on_close=lambda sender: self.set_opened(False), 
            show=self.opened
        ):
            dpg.add_text("Hello World")
    
    def render(self):
        pass