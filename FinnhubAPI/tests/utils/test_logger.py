import pytest
import os
import sys
import json
import time
import logging
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.utils.Logger import Logger

class TestLogger:
    """Test suite for the Logger class."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir)

    def test_init_defaults(self):
        """Test logger initialization with default values."""
        logger = Logger(name="test_logger")
        assert logger.name == "test_logger"
        assert logger.logger.level == logging.INFO
        assert len(logger.logger.handlers) == 1  # Console handler only

    def test_init_custom_params(self):
        """Test logger initialization with custom parameters."""
        logger = Logger(
            name="custom_logger",
            level=logging.DEBUG,
            log_to_console=True,
            log_to_file=True,
            log_file_path=self.log_file,
            max_file_size_mb=5,
            backup_count=3,
            format_string="%(levelname)s - %(message)s",
            json_format=False,
            capture_warnings=True,
            propagate=True
        )

        assert logger.name == "custom_logger"
        assert logger.logger.level == logging.DEBUG
        assert logger.logger.propagate is True
        assert len(logger.logger.handlers) == 2  # Console and file handlers

        # Verify file handler was created with correct path
        file_handlers = [h for h in logger.logger.handlers
                        if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) == 1
        assert file_handlers[0].baseFilename == self.log_file

    def test_json_format(self):
        """Test JSON formatting option."""
        logger = Logger(name="json_logger", json_format=True)
        assert logger.format_string == Logger.JSON_FORMAT

    def test_set_level(self):
        """Test changing log level."""
        logger = Logger(name="level_test", level=logging.INFO)
        assert logger.logger.level == logging.INFO

        logger.set_level(logging.DEBUG)
        assert logger.logger.level == logging.DEBUG

    def test_add_file_handler(self):
        """Test adding an additional file handler."""
        logger = Logger(name="handler_test")
        initial_handlers = len(logger.logger.handlers)

        logger.add_file_handler(self.log_file, level=logging.ERROR)

        assert len(logger.logger.handlers) == initial_handlers + 1
        file_handlers = [h for h in logger.logger.handlers
                        if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.ERROR

    def test_context_management(self):
        """Test context data management."""
        logger = Logger(name="context_test")

        # Add context
        logger.add_context("user", "test_user")
        logger.add_context("request_id", "123456")

        if hasattr(logger.context, 'data'):
            assert logger.context.data.get("user") == "test_user"
            assert logger.context.data.get("request_id") == "123456"

        # Remove specific context
        logger.remove_context("user")
        if hasattr(logger.context, 'data'):
            assert "user" not in logger.context.data
            assert "request_id" in logger.context.data

        # Clear all context
        logger.clear_context()
        if hasattr(logger.context, 'data'):
            assert not logger.context.data

    def test_format_with_context(self):
        """Test message formatting with context."""
        logger = Logger(name="format_test")

        # No context
        assert logger._format_with_context("Test message") == "Test message"

        # With context
        logger.add_context("user", "test_user")
        formatted = logger._format_with_context("Test message")
        assert formatted == "Test message [user=test_user]"

        # Multiple context items
        logger.add_context("request_id", "123456")
        formatted = logger._format_with_context("Test message")
        assert "Test message" in formatted
        assert "user=test_user" in formatted
        assert "request_id=123456" in formatted

    def test_basic_logging(self):
        """Test basic logging methods."""
        logger = Logger(
            name="basic_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Read log file contents
        with open(self.log_file, 'r') as f:
            contents = f.read()

        # Debug should not appear at default INFO level
        assert "Debug message" not in contents
        assert "Info message" in contents
        assert "Warning message" in contents
        assert "Error message" in contents
        assert "Critical message" in contents

    def test_exception_logging(self):
        """Test exception logging."""
        logger = Logger(
            name="exception_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Caught exception")

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Caught exception" in contents
        assert "ValueError: Test exception" in contents
        assert "Traceback" in contents

    def test_log_duration(self):
        """Test logging duration of tasks."""
        logger = Logger(
            name="duration_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        start_time = time.time()
        time.sleep(0.01)  # Short delay
        logger.log_duration(start_time, "test_task")

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Task 'test_task' completed in" in contents
        assert "seconds" in contents

    def test_context_manager(self):
        """Test the context manager functionality."""
        logger = Logger(
            name="ctx_mgr_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        # Test with context manager
        with logger.context_manager(request_id="12345", user="test_user"):
            logger.info("Inside context")
            if hasattr(logger.context, 'data'):
                assert logger.context.data.get("request_id") == "12345"
                assert logger.context.data.get("user") == "test_user"

        # Context should be cleared after exiting
        if hasattr(logger.context, 'data'):
            assert "request_id" not in logger.context.data
            assert "user" not in logger.context.data

        # Check log file
        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Inside context [" in contents
        assert "request_id=12345" in contents
        assert "user=test_user" in contents

    def test_timer_context_manager(self):
        """Test the timer context manager."""
        logger = Logger(
            name="timer_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        with logger.timer("timed_task"):
            time.sleep(0.01)  # Short delay

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Starting task: timed_task" in contents
        assert "Task 'timed_task' completed in" in contents
        assert "seconds" in contents

    def test_timer_with_exception(self):
        """Test timer context manager with exception."""
        logger = Logger(
            name="timer_exc_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        try:
            with logger.timer("failing_task"):
                time.sleep(0.01)  # Short delay
                raise ValueError("Timer test exception")
        except ValueError:
            pass

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Starting task: failing_task" in contents
        assert "Task 'failing_task' failed after" in contents
        assert "Timer test exception" in contents

    def test_logged_decorator(self):
        """Test the logged decorator."""
        logger = Logger(
            name="decorator_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        @logger.logged(log_args=True, log_result=True)
        def test_function(a, b):
            return a + b

        result = test_function(5, 7)
        assert result == 12

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Entering test_function with args: 5, 7" in contents
        assert "Exited test_function" in contents
        assert "with result: 12" in contents

    def test_timed_decorator(self):
        """Test the timed decorator."""
        logger = Logger(
            name="timed_decorator_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        @logger.timed()
        def slow_function():
            time.sleep(0.01)
            return "Done"

        result = slow_function()
        assert result == "Done"

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Function slow_function took" in contents
        assert "seconds" in contents

    def test_batch_logger(self):
        """Test batch logging functionality."""
        logger = Logger(
            name="batch_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        batch = logger.batch_logger(batch_size=3)

        batch.add("Message 1")
        batch.add("Message 2")

        # Check that nothing is logged yet (batch size not reached)
        with open(self.log_file, 'r') as f:
            contents = f.read()
        assert "Message 1" not in contents

        # Add one more to trigger batch logging
        batch.add("Message 3")

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Batch log (3 items)" in contents
        assert "Message 1" in contents
        assert "Message 2" in contents
        assert "Message 3" in contents

        # Test manual flush
        batch.add("Message 4")
        batch.flush()

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "Batch log (1 items)" in contents
        assert "Message 4" in contents

    def test_log_dict(self):
        """Test dictionary logging."""
        logger = Logger(
            name="dict_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        test_dict = {
            "user": "test_user",
            "id": 123,
            "timestamp": datetime.now(),
            "data": {
                "key1": "value1",
                "key2": "value2"
            }
        }

        logger.log_dict(test_dict, message="User data")

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "User data" in contents
        assert "test_user" in contents
        assert "123" in contents
        assert "key1" in contents
        assert "value1" in contents

    def test_log_startup_and_shutdown(self):
        """Test startup and shutdown logging."""
        logger = Logger(
            name="lifecycle_test",
            log_to_console=False,
            log_to_file=True,
            log_file_path=self.log_file
        )

        logger.log_startup()
        logger.log_shutdown()

        with open(self.log_file, 'r') as f:
            contents = f.read()

        assert "=== Application lifecycle_test starting up ===" in contents
        assert "Python version" in contents
        assert "Current time" in contents
        assert "Working directory" in contents

        assert "=== Application lifecycle_test shutting down ===" in contents
        assert "Uptime" in contents

    def test_get_underlying_logger(self):
        """Test retrieving the underlying logger."""
        logger = Logger(name="underlying_test")
        underlying = logger.get_underlying_logger()

        assert isinstance(underlying, logging.Logger)
        assert underlying.name == "underlying_test"
