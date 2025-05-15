from sources.core.decorators.athena_intern_lp import internal_log_profiling

import time
import platform

class AthenaLowLevelMandatory:
    if platform.system() == "Windows":
        import ctypes
        timeBeginPeriod = ctypes.windll.winmm.timeBeginPeriod
        timeEndPeriod = ctypes.windll.winmm.timeEndPeriod
        sleep = ctypes.windll.kernel32.Sleep
    else:
        timeBeginPeriod = lambda self, values: None
        timeEndPeriod = lambda self, values: None
        sleep = lambda self, ms: time.sleep(ms / 1000.0)
    
    def __init__(self, base: "ImGUIAthenaApp") -> None:
        self._base = base
    
    @internal_log_profiling(section="Athena Low Level")
    def do_task_period(self, callback: callable, period: int) -> None:
        self.timeBeginPeriod(period)
        callback()
        self.timeEndPeriod(period)
