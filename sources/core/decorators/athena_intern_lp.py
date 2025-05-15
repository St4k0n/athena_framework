# # Athena internal logs and profiling
from functools import wraps
from sources.core.utils.athena_colors import RESET, PURPLE, BLUE

import time

CORE_CONFIG = {
    "internal_logging": True,
    "internal_profiling": True,
}

def internal_log_profiling(section, specific_log : str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Access to self._base here, because self is available
            base = self._base
            
            func_name_colored = f"{PURPLE}{func.__name__}{RESET}"
            file_name = func.__code__.co_filename
            line_number = func.__code__.co_firstlineno + 1
            clickable_location = f"{file_name}:{line_number}"
            
            if base and base._logs:
                if CORE_CONFIG.get("internal_logging", True) and specific_log is None:
                    base._logs.ap.info(f"Starting {func_name_colored} in section {section} at {clickable_location}")
                    base._logs.ac.info(f"Starting {func_name_colored} in section {section} at {clickable_location}")
                    base._logs.flush_all()
                elif CORE_CONFIG.get("internal_logging", True) and specific_log is not None:
                    base._logs[specific_log].info(f"Starting {func_name_colored} in section {section} at {clickable_location}")
                    base._logs.flush_all()
                
                if CORE_CONFIG.get("internal_profiling", True):
                    start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
            except Exception as e:
                if base and CORE_CONFIG.get("internal_logging", True) and specific_log is None:
                    base._logs.ap.error(f"Error in {func_name_colored}: {e} at {clickable_location}")
                    base._logs.ac.error(f"Error in {func_name_colored}: {e} at {clickable_location}")
                    base._logs.flush_all()
                elif base and CORE_CONFIG.get("internal_logging", True) and specific_log is not None:
                    base._logs[specific_log].error(f"Error in {func_name_colored}: {e} at {clickable_location}")
                    base._logs.flush_all()
                raise
            finally:
                if base and CORE_CONFIG.get("internal_profiling", True) and specific_log is None:
                    elapsed_time = time.time() - start_time
                    base._logs.ac.info(f"{func_name_colored} in section {section} took {elapsed_time:.4f} seconds at {clickable_location}")
                    base._logs.ap.info(f"{func_name_colored} in section {section} took {elapsed_time:.4f} seconds at {clickable_location}")
                    base._logs.flush_all()
                elif base and CORE_CONFIG.get("internal_profiling", True) and specific_log is not None:
                    elapsed_time = time.time() - start_time
                    base._logs[specific_log].info(f"{func_name_colored} in section {section} took {elapsed_time:.4f} seconds at {clickable_location}")
                    base._logs.flush_all
            return result
        return wrapper
    return decorator


# CORE_CONFIG = {
#     "internal_logging": True,
#     "internal_profiling": True,
# }

# def internal_log_profiling(base : "ImGUIAthenaApp", section : str):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             if CORE_CONFIG.get("internal_logging", True):
#                 base._logs.ap.info(f"Starting {func.__name__} in section {section}")
#                 base._logs.ac.info(f"Starting {func.__name__} in section {section}")
            
#             if CORE_CONFIG.get("internal_profiling", True):
#                 start_time = time.time()
            
#             try:
#                 result = func(*args, **kwargs)
#             except Exception as e:
#                 if CORE_CONFIG.get("internal_logging", True):
#                     base._logs.ap.error(f"Error in {func.__name__}: {e}")
#                     base._logs.ac.error(f"Error in {func.__name__}: {e}")
#                 raise
#             finally:
#                 if CORE_CONFIG.get("internal_profiling", True):
#                     elapsed_time = time.time() - start_time
#                     base._logs.ac.info(f"{func.__name__} in section {section} took {elapsed_time:.4f} seconds")
#                     base._logs.ap.info(f"{func.__name__} in section {section} took {elapsed_time:.4f} seconds")
#             return result
#         return wrapper
#     return decorator
