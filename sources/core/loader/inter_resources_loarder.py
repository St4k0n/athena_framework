from sources.core.decorators.athena_intern_lp import internal_log_profiling
import os, json, dearpygui.dearpygui as dpg


class AthenaResourceLoader:
    def __init__(self, base : "ImGUIAthenaApp" = None,  resoure_directory : str = "./assets/resources"):
        assert base is not None, "AthenaResourceLoader must be initialized with a base ImGUIAthenaApp instance"
        assert os.path.exists(resoure_directory), f"Resource directory {resoure_directory} does not exist"
        
        self._base = base
        self.resource_directory = resoure_directory
        self.resources = {
            "fonts": [],
            "textures": [],
            "themes": []
        } # dictionary to store the resources
        
    @internal_log_profiling(section="AthenaResourceLoader", specific_log="alr")
    def load_resources(self):
        for filename in os.listdir(self.resource_directory):
            if filename.endswith(".rloader.json"):
                self.load_resource_file(os.path.join(self.resource_directory, filename))

    @internal_log_profiling(section="AthenaResourceLoader", specific_log="alr")
    def load_resource_file(self, filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
            for resource_type in self.resources.keys():
                if resource_type in data:
                    self.resources[resource_type].extend(data[resource_type])

    @internal_log_profiling(section="AthenaResourceLoader", specific_log="alr")
    def _convert_to_dpg_constant(self, name):
        try:
            return getattr(dpg, name)
        except AttributeError:
            raise ValueError(f"Invalid Dear PyGui constant: {name}")

    @internal_log_profiling(section="AthenaResourceLoader", specific_log="alr")
    def apply_resources(self):
        with dpg.font_registry():
            for font in self.resources["fonts"]:
                _font = dpg.add_font(file=font["path"], size=font["size"], tag=font.get("tag", "default_font"))
                self._base._meta_data["fonts"][font["tag"]] = _font
        
        for texture in self.resources["textures"]:
            with dpg.texture_registry():
                width, height, channels, data = dpg.load_image(texture["path"])
                if texture.get("dynamic", False):
                    _texture = dpg.add_dynamic_texture(width, height, data, tag=texture.get("tag", ""))
                else:
                    _texture = dpg.add_static_texture(width, height, data, tag=texture.get("tag", ""))
                self._base._meta_data["images"].append({
                    "width": width,
                    "height": height,
                    "channels": channels,
                    "data": data,
                    "tag": texture["tag"],
                    "texture": _texture
                })

        for theme in self.resources["themes"]:
            with dpg.theme(tag=theme["tag"]):
                for component in theme["components"]:
                    target = self._convert_to_dpg_constant(component.get("target", "mvAll"))
                    with dpg.theme_component(target):
                        for color in component.get("colors", []):
                            color_name = self._convert_to_dpg_constant(color["name"])
                            dpg.add_theme_color(color_name, color["value"], category=self._convert_to_dpg_constant(color.get("category", "mvThemeCat_Core")))
                        for style in component.get("styles", []):
                            style_name = self._convert_to_dpg_constant(style["name"])
                            if isinstance(style["value"], list) and len(style["value"]) == 2:
                                dpg.add_theme_style(style_name, style["value"][0], style["value"][1], category=self._convert_to_dpg_constant(style.get("category", "mvThemeCat_Core")))
                            else:
                                dpg.add_theme_style(style_name, style["value"], category=self._convert_to_dpg_constant(style.get("category", "mvThemeCat_Core")))
                        # for font in component.get("fonts", []):
                            # dpg.set_theme_font(font["tag"])

"""
class ResourceLoader:
    def __init__(self, resource_directory):
        self.resource_directory = resource_directory
        self.resources = {
            "fonts": [],
            "textures": [],
            "themes": []
        }

    def load_resources(self):
        for filename in os.listdir(self.resource_directory):
            if filename.endswith(".rloader.json"):
                self.load_resource_file(os.path.join(self.resource_directory, filename))

    def load_resource_file(self, filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
            for resource_type in self.resources.keys():
                if resource_type in data:
                    self.resources[resource_type].extend(data[resource_type])

    def apply_resources(self):
        for font in self.resources["fonts"]:
            dpg.add_font(font["path"], font["size"], tag=font.get("tag", "default_font"))
        
        for texture in self.resources["textures"]:
            if texture.get("dynamic", False):
                dpg.add_dynamic_texture(texture["width"], texture["height"], texture["data"], tag=texture.get("tag", ""))
            else:
                dpg.load_image(texture["path"], texture["width"], texture["height"], tag=texture.get("tag", ""))

        for theme in self.resources["themes"]:
            with dpg.theme(tag=theme["tag"]):
                for component in theme["components"]:
                    target = component.get("target", dpg.mvAll)
                    with dpg.theme_component(target):
                        for color in component.get("colors", []):
                            dpg.add_theme_color(color["name"], color["value"], category=color.get("category", dpg.mvThemeCat_Core))
                        for style in component.get("styles", []):
                            dpg.add_theme_style(style["name"], style["value"], category=style.get("category", dpg.mvThemeCat_Core))

    def debug_print(self):
        for resource_type, resources in self.resources.items():
            print(f"{resource_type.capitalize()}: {resources}")
"""