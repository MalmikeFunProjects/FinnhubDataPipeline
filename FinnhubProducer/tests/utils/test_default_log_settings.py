import pytest
import logging
from unittest.mock import patch, MagicMock
from app.utils.Logger import Logger
from app.utils.default_log_setting import DefaultLogger
from app.utils import default_log_setting

class TestDefaultLogger:
    def test_get_logger_default_parameters(self):
        """Test get_logger with default parameters."""
        mock_logger = MagicMock()
        with patch.object(default_log_setting, 'Logger', mock_logger):
            logger = DefaultLogger.get_logger()
            mock_logger.assert_called_once_with(
                name=None,
                level=logging.INFO,
                log_to_console=True,
                log_to_file=False,
                log_file_path=None
            )

    def test_get_logger_custom_parameters(self):
        """Test get_logger with custom parameters."""
        mock_logger = MagicMock()
        with patch.object(default_log_setting, 'Logger', mock_logger):
            logger = DefaultLogger.get_logger(
                name="test_logger",
                level=logging.DEBUG,
                log_to_console=False,
                log_to_file=True,
                log_file_path="/tmp/test.log",
                custom_param="value"
            )
            mock_logger.assert_called_once_with(
                name="test_logger",
                level=logging.DEBUG,
                log_to_console=False,
                log_to_file=True,
                log_file_path="/tmp/test.log",
                custom_param="value"
            )

    def test_integration_get_logger(self):
        """Integration test for get_logger method."""
        logger = DefaultLogger.get_logger(name="integration_test")
        assert isinstance(logger, Logger)
        assert logger.get_underlying_logger().name == "integration_test"

    def test_integration_get_err_logger(self):
        """Integration test for get_err_logger method."""
        logger = DefaultLogger.get_err_logger(name="error_integration_test")
        assert isinstance(logger, Logger)

        # Get the underlying logger
        underlying_logger = logger.get_underlying_logger()

        # Check name
        assert underlying_logger.name == "error_integration_test"

        # Count handlers - should be at least one more than the base logger
        base_logger = DefaultLogger.get_logger(name="base_test")
        base_handler_count = len(base_logger.get_underlying_logger().handlers)
        err_handler_count = len(underlying_logger.handlers)

        # The error logger should have at least one additional handler
        assert err_handler_count > base_handler_count

        # Find the error handler
        error_handlers = [h for h in underlying_logger.handlers if h.level == logging.ERROR]
        assert len(error_handlers) >= 1
