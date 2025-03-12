import threading
from .singleton import Singleton

class FunctionTimer(metaclass=Singleton):
    def __init__(self):
        self.running_timers = {}

    def __trigger_action_after_duration(self, timer_name: str, duration: int, action: callable, *args, **kwargs):
        timer = threading.Timer(duration, action, *args, **kwargs)
        self.running_timers[timer_name] = timer
        timer.start()

    def cancel_timer(self, timer_name: str):
        if timer_name in self.running_timers:
            self.running_timers[timer_name].cancel()
            del self.running_timers[timer_name]

    def cancel_all_timers(self):
        for timer in self.running_timers.values():
            timer.cancel()
        self.running_timers.clear()

    def run_timer_if_not_exist(self, timer_name: str, duration: int, action: callable, *args, **kwargs):
        if(timer_name not in self.running_timers):
            self.__trigger_action_after_duration(timer_name, duration, action, *args, **kwargs)

    def reset_timer(self, timer_name: str, duration: int, action: callable, *args, **kwargs):
        if(timer_name in self.running_timers):
            self.cancel_timer(timer_name)
        self.__trigger_action_after_duration(timer_name, duration, action, *args, **kwargs)

    def is_timer_running(self, timer_name: str) -> bool:
        if(timer_name in self.running_timers):
            return self.running_timers[timer_name].is_alive()
        else:
            return False

