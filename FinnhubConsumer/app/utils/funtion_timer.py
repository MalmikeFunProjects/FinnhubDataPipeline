import threading
import time
from .singleton import Singleton

from utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("function_timer", log_to_console=True)


class TrackedTimer(threading.Timer):
    """Extended Timer class that tracks execution time and status."""

    def __init__(self, interval, function, name="", *args, **kwargs):
        super().__init__(interval, function, *args, **kwargs)
        self.start_time = None
        self.elapsed_time = 0
        self.name = name

    def start(self):
        """Start the timer and record start time."""
        logger.info(f"Starting timer: {self.name}")
        self.start_time = time.time()
        super().start()

    def run(self):
        """Execute the function and cleanup when done."""
        super().run()
        self.elapsed_time = time.time() - self.start_time if self.start_time else 0
        logger.info(f"Running timer: {self.name} at {self.elapsed_time:.2f}s")

        # Get the singleton instance and remove this timer from running timers
        function_timer = FunctionTimer()
        if self.name in function_timer.running_timers:
            del function_timer.running_timers[self.name]

        self.start_time = None
        self.elapsed_time = 0

    def cancel(self):
        """Cancel the timer and cleanup."""
        elapsed = self.get_elapsed_time()
        super().cancel()
        logger.info(f"Cancelling timer: {self.name} at {elapsed:.2f}s")
        self.start_time = None
        self.elapsed_time = 0

    def is_alive(self):
        """Check if the timer is still active or has completed."""
        return super().is_alive() or self.elapsed_time > 0

    def get_elapsed_time(self):
        """Get the elapsed time since timer start."""
        if self.start_time is None:
            return 0  # Timer hasn't started yet
        elif self.elapsed_time == 0 and self.is_alive():
            return time.time() - self.start_time# Timer is still running
        else:
            return self.elapsed_time


class FunctionTimer(metaclass=Singleton):
    """Singleton class to manage multiple timers."""

    def __init__(self):
        self.running_timers = {}

    def __trigger_action_after_duration(self, timer_name, duration, action, *args, **kwargs):
        """Internal method to create and start a new timer."""
        timer = TrackedTimer(
            interval=duration,
            function=action,
            name=timer_name,
            *args,
            **kwargs
        )
        self.running_timers[timer_name] = timer
        timer.start()

    def cancel_timer(self, timer_name):
        """Cancel a specific timer by name."""
        if timer_name in self.running_timers:
            self.running_timers[timer_name].cancel()
            try:
                del self.running_timers[timer_name]
            except KeyError as e:
                logger.error(f"KeyError in cancel_timer: {e}")

    def cancel_all_timers(self):
        """Cancel all running timers."""
        for timer in list(self.running_timers.values()):
            timer.cancel()
        self.running_timers.clear()

    def run_timer_if_not_exist(self, timer_name, duration, action, *args, **kwargs):
        """Start a timer only if one with the same name doesn't exist."""
        if timer_name not in self.running_timers:
            self.__trigger_action_after_duration(timer_name, duration, action, *args, **kwargs)

    def reset_timer(self, timer_name, duration, action, *args, **kwargs):
        """Cancel an existing timer and start a new one with the same name."""
        if timer_name in self.running_timers:
            self.cancel_timer(timer_name)
        self.__trigger_action_after_duration(timer_name, duration, action, *args, **kwargs)

    def is_timer_running(self, timer_name):
        """Check if a timer with the given name is currently running."""
        return (timer_name in self.running_timers and
                self.running_timers[timer_name].is_alive())

    def get_elapsed_time(self, timer_name):
        """Get the elapsed time for a specific timer."""
        if timer_name in self.running_timers:
            return self.running_timers[timer_name].get_elapsed_time()
        return 0
