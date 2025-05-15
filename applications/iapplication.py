import dearpygui.dearpygui as dpg

# Each application have multiple dpg content

example_application_save = {
    "_base": {
        "name": "example_application",
        "version": "0.0.1",
        "opened": False,
    },
    "_dpg_meta_data": {
        "background_window": {
            "pos": [0, 0],
            "width": 0,
        }
    }
}

class IApplication:
    def __init__(
        self,
        base: "ImGUIAthenaApp",
        name: str,
        version: str,
        opened: bool = False,
        **kwargs
    ) -> None:
        self._base = base

        self.name = name
        self.tag_window = f"{self.name}_application_window"
        self.version = version
        self.opened = opened
        self.pre_mount()

        self._need_update = False

    def set_need_update(self, need_update: bool):
        self._need_update = need_update
        
    def set_opened(self, opened: bool):
        self.opened = opened
        dpg.configure_item(self.tag_window, show=self.opened)
        
    def pre_mount(self):
        _application_dir = f"applications/{self.name}"
        _application_icon = f"{_application_dir}/assets/icon.png"
        
        with dpg.texture_registry(show=False):
            width, height, channels, data = dpg.load_image(_application_icon)
            self._base._meta_data["images"].append({
                "tag": f"{self.name}_application_icon",
                "width": width,
                "height": height,
                "channels": channels,
                "data": data,
            })
            dpg.add_static_texture(width, height, data, tag=f"{self.name}_application_icon")
    
    def update(self):
        raise NotImplementedError
    
    def mount(self):
        raise NotImplementedError
    
    def render(self):
        raise NotImplementedError
    
    def save(self):
        raise NotImplementedError
    
    def load(self):
        raise NotImplementedError

    def delete(self):
        dpg.delete_item(f"{self.name}_application_icon")
        dpg.delete_item(f"{self.name}_application_window")

    def __str__(self) -> str:
        return f"{self.name} - {self.version}, opened: {self.opened}"