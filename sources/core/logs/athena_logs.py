import spdlog as spd
import os

class AthenaLogs:
    logLevel = {
        "trace": spd.LogLevel.TRACE,
        "debug": spd.LogLevel.DEBUG,
        "info": spd.LogLevel.INFO,
        "warn": spd.LogLevel.WARN,
    }
    
    def create_console_logger(self, name, log_level=spd.LogLevel.INFO, pattern="[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] %v"):
        logger = spd.ConsoleLogger(name)
        logger.set_pattern(pattern)
        logger.set_level(log_level)
        return logger
    
    def create_file_logger(self, name, path, log_level=spd.LogLevel.INFO, rewrite=False, pattern="[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] %v"):
        if rewrite and os.path.exists(path):
            os.remove(path)
        logger = spd.FileLogger(name, path, False)
        logger.set_pattern(pattern)
        logger.set_level(log_level)
        return logger
    
    def __init__(self):
        self._loggers = {
            "athena_process": self.create_file_logger("athena_process", "logs/athena_process.log", rewrite=True),
            "athena_console": self.create_console_logger("athena_console"),
        }
        self._abbrev_loggers = {}
        self._initialize_abbreviations()

    def _initialize_abbreviations(self):
        for name in self._loggers:
            abbrev_name = ''.join([word[0] for word in name.split('_')])
            self._abbrev_loggers[abbrev_name] = self._loggers[name]
    
    def __getitem__(self, key):
        if key in self._loggers:
            return self._loggers[key]
        elif key in self._abbrev_loggers:
            return self._abbrev_loggers[key]
        else:
            raise KeyError(f"Logger '{key}' not found.")
    
    def _create_dynamic_property(self, name):
        abbrev_name = ''.join([word[0] for word in name.split('_')])
        setattr(self.__class__, abbrev_name, property(lambda self, name=name: self._loggers[name]))
        self._abbrev_loggers[abbrev_name] = self._loggers[name]
    
    def add_update_logger(self, name, logger):
        self._loggers[name] = logger
        self._create_dynamic_property(name)
    
    @property
    def ap(self):
        return self._loggers["athena_process"]

    @property
    def ac(self):
        return self._loggers["athena_console"]
    
    def flush_all(self):
        for logger in self._loggers.values():
            logger.flush()
            