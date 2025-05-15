from sources.core.decorators.athena_intern_lp import internal_log_profiling

import dearpygui.dearpygui as dpg
import json
import os


class AthenaProfilesUtils:
    _base : "ImGUIAthenaApp" = None
    
    def __init__(self, base) -> None:
        self._base = base
        self._logs = base._logs
        self._base_config_profiles = None
        self._profile = None

    @property
    def profile(self):
        return self._profile

    @property
    def name(self):
        if self._profile is None:
            self._logs.ap.critical("Profile not found [name]")
            return None
        return self._profile["name"]
    
    @property
    def path(self):
        if self._profile is None:
            self._logs.ap.critical("Profile not found [path]")
            return None
        return self._profile["path"]
    
    @property
    def init_file(self):
        if self._profile is None:
            self._logs.ap.critical("Profile not found [init_file]")
            return None
        return self._profile["init_file"]

    @property
    def bcp(self):
        return self._base_config_profiles

    @internal_log_profiling(section="Athena Profiles Utils")
    def load_base_config_profiles(self) -> "AthenaProfilesUtils":
        assert self._base_config_profiles is None, "Base config profiles already loaded"
        assert os.path.exists("profiles/_base_config_profiles.json"), "Base config profiles not found"
        
        with open("profiles/_base_config_profiles.json", "r") as fd:
            self._base_config_profiles = json.load(fd)
        return self
    
    @internal_log_profiling(section="Athena Profiles Utils")
    def save_base_config_profiles(self):
        with open("profiles/_base_config_profiles.json", "w") as fd:
            json.dump(self._base_config_profiles, fd, indent=4)
    
    
    @internal_log_profiling(section="Athena Profiles Utils")
    def get_profiles_names(self):
        assert self._base_config_profiles is not None, "Base config profiles not loaded"
        # get list of files in profiles/stream
        profiles = os.listdir("profiles/stream")
        profiles = [profile.split(".")[0] for profile in profiles if profile.endswith(".json")]
        return profiles
    
    @internal_log_profiling(section="Athena Profiles Utils")
    def create_profile(self, profile_name: str):
        return {
            "name": profile_name,
            "path": f"profiles/stream/{profile_name}.json",
            "init_file": f"profiles/stream/{profile_name}.ini",
            "meta": {
            }
        }
    
    @internal_log_profiling(section="Athena Profiles Utils")
    def save_profile(self):
        if self._profile is None:
            self._logs.ap.critical("Profile not found")
            self._logs.ac.critical("Profile not found")
            self._logs.flush_all()
            return
        with open(self._profile["path"], "w") as fd:
            json.dump(self._profile, fd, indent=4)
        dpg.save_init_file(self._profile["init_file"])
        self._logs.ac.info(f"Profile {self._profile['name']} saved successfully")
        self._logs.ap.info(f"Profile {self._profile['name']} saved successfully")
        self._logs.flush_all()
    
    @internal_log_profiling(section="Athena Profiles Utils")
    def load_profile(self, profile_name: str):
        try:
            assert self._base_config_profiles is not None, "Base config profiles not loaded"
            assert profile_name in self.get_profiles_names(), f"Profile {profile_name} not found"
            
            with open(f"profiles/stream/{profile_name}.json", "r") as fd:
                self._profile = json.load(fd)
            self._logs.ac.info(f"Profile {profile_name} loaded successfully")
            self._logs.ap.info(f"Profile {profile_name} loaded successfully")
        except Exception as e:
            self._logs.ap.critical(str(e) + " [load_profile]")
            self._logs.ac.critical(str(e) + " [load_profile]")
        self._logs.flush_all()
    
    @internal_log_profiling(section="Athena Profiles Utils")
    def setup_profile(self, profile: dict):
        try:
            assert "name" in profile, "Profile name not found"
            assert "path" in profile, "Profile path not found"
            assert "init_file" in profile, "Profile init file not found"
            
            with open(profile["path"], "w") as fd:
                json.dump(profile, fd, indent=4)
                
            if os.path.exists(profile["init_file"]):
                dpg.configure_app(init_file=profile["init_file"])
                # dpg.load_init_file(profile["init_file"])
                
            dpg.save_init_file(profile["init_file"])
            self._logs.ac.info(f"Profile {profile['name']} setup successfully")
            self._logs.ap.info(f"Profile {profile['name']} setup successfully")
            
            self._profile = profile
        except Exception as e:
            self._logs.ap.critical(str(e) + " [setup_profile]")
            self._logs.ac.critical(str(e) + " [setup_profile]")
        self._logs.flush_all()
        