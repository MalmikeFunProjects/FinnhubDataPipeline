import time
import pytest
from app.utils.funtion_timer import FunctionTimer, TrackedTimer

class TestTrackedTimer:
    def test_timer_executes_function(self):
        result = []

        def sample_action():
            result.append("executed")

        timer = TrackedTimer(interval=0.1, function=sample_action, name="test1")
        timer.start()
        timer.join()  # Wait for timer to finish

        assert "executed" in result
        assert timer.get_elapsed_time() == 0  # Elapsed time reset after run
        assert not timer.is_alive()

    def test_timer_cancel_before_execution(self):
        result = []

        def sample_action():
            result.append("executed")

        timer = TrackedTimer(interval=0.3, function=sample_action, name="test_cancel")
        timer.start()
        time.sleep(0.1)
        timer.cancel()
        time.sleep(0.3)

        assert "executed" not in result
        assert timer.get_elapsed_time() == 0

    def test_elapsed_time_tracking(self):
        def dummy():
            pass

        timer = TrackedTimer(interval=0.2, function=dummy, name="test_elapsed")
        timer.start()
        time.sleep(0.1)
        assert 0 < timer.get_elapsed_time() < 0.2
        timer.cancel()


class TestFunctionTimer:
    def setup_method(self):
        self.timer_manager = FunctionTimer()
        self.timer_manager.cancel_all_timers()  # Clear timers before each test

    def test_run_timer_if_not_exist(self):
        result = []

        def action():
            result.append("ran")

        self.timer_manager.run_timer_if_not_exist("timer1", 0.1, action)
        time.sleep(0.2)
        assert "ran" in result

    def test_run_timer_if_exists_does_nothing(self):
        result = []

        def action():
            result.append("ran")

        self.timer_manager.run_timer_if_not_exist("timer2", 0.3, action)
        self.timer_manager.run_timer_if_not_exist("timer2", 0.3, action)
        time.sleep(0.4)
        assert result.count("ran") == 1

    def test_reset_timer(self):
        result = []

        def action():
            result.append("ran")

        self.timer_manager.run_timer_if_not_exist("timer3", 0.3, action)
        time.sleep(0.1)
        self.timer_manager.reset_timer("timer3", 0.1, action)
        time.sleep(0.3)
        assert result.count("ran") == 1

    def test_cancel_timer(self):
        result = []

        def action():
            result.append("ran")

        self.timer_manager.run_timer_if_not_exist("timer4", 0.3, action)
        time.sleep(0.1)
        self.timer_manager.cancel_timer("timer4")
        time.sleep(0.3)
        assert "ran" not in result

    def test_cancel_all_timers(self):
        result = []

        def action():
            result.append("ran")

        self.timer_manager.run_timer_if_not_exist("timer5", 0.3, action)
        self.timer_manager.run_timer_if_not_exist("timer6", 0.3, action)
        time.sleep(0.1)
        self.timer_manager.cancel_all_timers()
        time.sleep(0.3)
        assert "ran" not in result

    def test_is_timer_running(self):
        def dummy():
            pass

        self.timer_manager.run_timer_if_not_exist("timer7", 0.3, dummy)
        assert self.timer_manager.is_timer_running("timer7") is True
        time.sleep(0.4)
        assert self.timer_manager.is_timer_running("timer7") is False

    def test_get_elapsed_time(self):
        def dummy():
            pass

        self.timer_manager.run_timer_if_not_exist("timer8", 0.3, dummy)
        time.sleep(0.1)
        elapsed = self.timer_manager.get_elapsed_time("timer8")
        assert 0 < elapsed < 0.3
