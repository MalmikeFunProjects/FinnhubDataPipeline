# Create a main application logger
from app.utils.Logger import Logger
import logging
import sys

class DefaultLogger:

    @staticmethod
    def get_logger(
        name: str = None,
        level: int = logging.INFO,
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_file_path: str = None,
        **kwargs
    ) -> Logger:
        """
        Get a preconfigured logger instance.

        Args:
            name: Logger name
            level: Minimum log level
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
            log_file_path: Path to log file
            **kwargs: Additional arguments to pass to Logger constructor

        Returns:
            A configured Logger instance
        """
        return Logger(
            name=name,
            level=level,
            log_to_console=log_to_console,
            log_to_file=log_to_file,
            log_file_path=log_file_path,
            **kwargs
        )

    @staticmethod
    def get_err_logger(
        name: str = None,
        level: int = logging.INFO,
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_file_path: str = None,
        **kwargs
        ) -> Logger:
            """
            Get a preconfigured logger instance with detailed error logging.

            Args:
                name: Logger name
                level: Minimum log level
                log_to_console: Whether to log to console
                log_to_file: Whether to log to file
                log_file_path: Path to log file
                **kwargs: Additional arguments to pass to Logger constructor

            Returns:
                A configured Logger instance
            """
            logger = DefaultLogger.get_logger(
                name=name,
                level=level,
                log_to_console=log_to_console,
                log_to_file=log_to_file,
                log_file_path=log_file_path,
                **kwargs
            )
            # Get the underlying logger to add a specialized error handler
            underlying_logger = logger.get_underlying_logger()

            # Create a specialized handler for errors with a more detailed format
            error_handler = logging.StreamHandler(sys.stdout)
            error_handler.setLevel(logging.ERROR)  # Only capture ERROR and above
            error_formatter = logging.Formatter(logger.DETAILED_FORMAT)  # Use the detailed format for errors
            error_handler.setFormatter(error_formatter)
            underlying_logger.addHandler(error_handler)
            return logger
