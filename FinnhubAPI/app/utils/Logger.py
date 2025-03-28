"""
robust_logger.py - A comprehensive logging module for Python applications

This module provides a flexible and feature-rich logging system with:
- Multiple output destinations (console, file, rotating files)
- Customizable formatting
- Log level filtering
- Context-based logging
- Performance metrics
- Exception tracking
"""

import logging
import logging.handlers
import os
import sys
import time
import functools
import threading
import json
from datetime import datetime
from typing import Dict, Any


class Logger:
    """
    A robust logging system that provides comprehensive logging capabilities
    with multiple outputs and formatting options.
    """

    # Standard log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    # Default format strings
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    JSON_FORMAT = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'

    def __init__(
        self,
        name: str = None,
        level: int = logging.INFO,
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_file_path: str = None,
        max_file_size_mb: int = 10,
        backup_count: int = 5,
        format_string: str = None,
        json_format: bool = False,
        capture_warnings: bool = True,
        propagate: bool = False
    ):
        """
        Initialize the logger with the specified configuration.

        Args:
            name: Logger name (defaults to module name)
            level: Minimum log level to record
            log_to_console: Whether to output logs to console
            log_to_file: Whether to output logs to a file
            log_file_path: Path to the log file (required if log_to_file is True)
            max_file_size_mb: Maximum size of log file before rotation (in MB)
            backup_count: Number of backup files to keep
            format_string: Custom format string for log messages
            json_format: Whether to format log messages as JSON
            capture_warnings: Whether to capture Python warnings
            propagate: Whether to propagate logs to parent loggers
        """
        # Set up the logger name
        self.name = name or os.path.basename(sys.argv[0]).split('.')[0]
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level)
        self.logger.propagate = propagate

        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Determine format
        if json_format:
            self.format_string = self.JSON_FORMAT
        else:
            self.format_string = format_string or self.DEFAULT_FORMAT

        self.formatter = logging.Formatter(self.format_string)

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if log_to_file:
            if not log_file_path:
                # Default log file path
                log_dir = "logs"
                os.makedirs(log_dir, exist_ok=True)
                log_file_path = os.path.join(log_dir, f"{self.name}.log")

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(log_file_path)), exist_ok=True)

            # Use RotatingFileHandler for automatic log rotation
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count
            )
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)

        # Capture warnings if specified
        if capture_warnings:
            logging.captureWarnings(True)

        # Context storage using thread local storage
        self.context = threading.local()
        self.context.data = {}

        # Store the start time for performance measurement
        self.start_time = time.time()

    def set_level(self, level: int) -> None:
        """Set the logging level."""
        self.logger.setLevel(level)

    def add_file_handler(
        self,
        file_path: str,
        level: int = None,
        formatter: logging.Formatter = None,
        max_size_mb: int = 10,
        backup_count: int = 5
    ) -> None:
        """
        Add an additional file handler.

        Args:
            file_path: Path to the log file
            level: Log level for this handler (defaults to logger's level)
            formatter: Custom formatter for this handler
            max_size_mb: Maximum size of log file before rotation (in MB)
            backup_count: Number of backup files to keep
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )

        if level:
            handler.setLevel(level)

        handler.setFormatter(formatter or self.formatter)
        self.logger.addHandler(handler)

    def add_context(self, key: str, value: Any) -> None:
        """Add a key-value pair to the logging context."""
        if not hasattr(self.context, 'data'):
            self.context.data = {}
        self.context.data[key] = value

    def remove_context(self, key: str) -> None:
        """Remove a key from the logging context."""
        if hasattr(self.context, 'data') and key in self.context.data:
            del self.context.data[key]

    def clear_context(self) -> None:
        """Clear all context data."""
        if hasattr(self.context, 'data'):
            self.context.data = {}

    def _format_with_context(self, message: str) -> str:
        """Format the message with the current context."""
        if hasattr(self.context, 'data') and self.context.data:
            context_str = " ".join([f"{k}={v}" for k, v in self.context.data.items()])
            return f"{message} [{context_str}]"
        return message

    # Standard logging methods
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(self._format_with_context(message), *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(self._format_with_context(message), *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(self._format_with_context(message), *args, **kwargs)

    def error(self, message: str, *args, exc_info=None, stack_info=False, **kwargs) -> None:
        """Log an error message."""
        if exc_info is True and sys.exc_info()[0] is not None:
            self.logger.error(
                self._format_with_context(message),
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                **kwargs
            )
        else:
            self.logger.error(self._format_with_context(message), *args, **kwargs)

    def critical(self, message: str, *args, exc_info=True, stack_info=True, **kwargs) -> None:
        """Log a critical message with exception and stack info by default."""
        self.logger.critical(
            self._format_with_context(message),
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            **kwargs
        )

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log an exception message (includes exception info)."""
        self.logger.exception(self._format_with_context(message), *args, **kwargs)

    # Performance logging
    def log_duration(self, start_time: float, task_name: str, level: int = logging.INFO) -> None:
        """Log the duration of a task."""
        duration = time.time() - start_time
        self.logger.log(
            level,
            self._format_with_context(f"Task '{task_name}' completed in {duration:.4f} seconds")
        )

    # Context managers
    def context_manager(self, **context_data):
        """Context manager for adding temporary context data to logs."""
        class LoggingContextManager:
            def __init__(self, logger_instance):
                self.logger = logger_instance
                self.context_data = context_data
                self.previous_data = {}

            def __enter__(self):
                # Save previous values
                for key, value in self.context_data.items():
                    if hasattr(self.logger.context, 'data') and key in self.logger.context.data:
                        self.previous_data[key] = self.logger.context.data[key]
                    self.logger.add_context(key, value)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                # Restore previous values
                for key in self.context_data:
                    if key in self.previous_data:
                        self.logger.add_context(key, self.previous_data[key])
                    else:
                        self.logger.remove_context(key)

                # Log exception if one occurred
                if exc_type is not None:
                    self.logger.exception(f"Exception occurred: {exc_val}")
                    return False  # Re-raise the exception
                return True

        return LoggingContextManager(self)

    def timer(self, task_name: str, level: int = logging.INFO):
        """Context manager for timing execution of code blocks."""
        class TimerContextManager:
            def __init__(self, logger_instance, task, log_level):
                self.logger = logger_instance
                self.task = task
                self.level = log_level

            def __enter__(self):
                self.start_time = time.time()
                self.logger.log(self.level, f"Starting task: {self.task}")
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time if self.start_time else 0
                if exc_type is not None:
                    self.logger.log(
                        logging.ERROR,
                        f"Task '{self.task}' failed after {duration:.4f} seconds: {exc_val}"
                    )
                    return False
                else:
                    self.logger.log(
                        self.level,
                        f"Task '{self.task}' completed in {duration:.4f} seconds"
                    )
                return True

        return TimerContextManager(self, task_name, level)

    # Decorators
    def logged(self, level=logging.INFO, log_args=False, log_result=False):
        """Decorator to log function entry/exit with optional argument and result logging."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_name = func.__name__

                # Log function entry
                entry_msg = f"Entering {func_name}"
                if log_args and (args or kwargs):
                    arg_str = ", ".join([str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()])
                    entry_msg += f" with args: {arg_str}"
                self.logger.log(level, entry_msg)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    # Log function exit
                    exit_msg = f"Exited {func_name} in {duration:.4f}s"
                    if log_result:
                        exit_msg += f" with result: {result}"
                    self.logger.log(level, exit_msg)

                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    self.logger.exception(
                        f"Exception in {func_name} after {duration:.4f}s: {str(e)}"
                    )
                    raise

            return wrapper

        return decorator

    def timed(self, level=logging.INFO):
        """Decorator to time function execution."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_name = func.__name__
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.logger.log(level, f"Function {func_name} took {duration:.4f} seconds")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.logger.exception(
                        f"Exception in {func_name} after {duration:.4f}s: {str(e)}"
                    )
                    raise

            return wrapper

        return decorator

    # Batch logging
    def batch_logger(self, batch_size=10, level=logging.INFO):
        """
        Creates a batch logger that collects messages and logs them in batches.
        Useful for high-frequency logging to reduce I/O overhead.
        """
        class BatchLogger:
            def __init__(self, logger_instance, batch_size, level):
                self.logger = logger_instance
                self.batch_size = batch_size
                self.level = level
                self.messages = []

            def add(self, message):
                self.messages.append(message)
                if len(self.messages) >= self.batch_size:
                    self.flush()

            def flush(self):
                if self.messages:
                    combined_message = "\n".join(self.messages)
                    self.logger.log(self.level, f"Batch log ({len(self.messages)} items):\n{combined_message}")
                    self.messages = []

            def __del__(self):
                self.flush()

        return BatchLogger(self, batch_size, level)

    # Additional utility methods
    def log_dict(self, data: Dict[str, Any], message: str = None, level: int = logging.INFO) -> None:
        """Log a dictionary as a formatted JSON string."""
        if message:
            log_message = f"{message}: {json.dumps(data, default=str, indent=2)}"
        else:
            log_message = json.dumps(data, default=str, indent=2)
        self.logger.log(level, log_message)

    def log_exception(self, exc: Exception, message: str = None) -> None:
        """Log an exception with traceback."""
        if message:
            self.exception(f"{message}: {str(exc)}")
        else:
            self.exception(str(exc))

    def log_startup(self) -> None:
        """Log application startup information."""
        self.info(f"=== Application {self.name} starting up ===")
        self.info(f"Python version: {sys.version}")
        self.info(f"Current time: {datetime.now().isoformat()}")
        self.info(f"Working directory: {os.getcwd()}")

    def log_shutdown(self) -> None:
        """Log application shutdown information."""
        uptime = time.time() - self.start_time if self.start_time else 0
        self.info(f"=== Application {self.name} shutting down ===")
        self.info(f"Uptime: {uptime:.2f} seconds")

    def get_underlying_logger(self) -> logging.Logger:
        """Get the underlying Python logger instance."""
        return self.logger
