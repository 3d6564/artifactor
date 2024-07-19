import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from functools import wraps
from .helpers import check_and_create_directory


class Logger:
    """
    Logger class to handle logging for all actions and events.

    This class provides methods to configure logging, log actions, generate the log,
    and write to the log.

    Attributes:
        logger (logging.Logger): The logger instance for logging messages.
    """

    def __init__(self):
        """
        Initialize the Logger instance and configure the log.
        """
        self.logger = None
        self.generate_activity_log()

    def log_action(self, func):
        """
        Decorator to log the execution and result of a function.

        Args:
            func (function): The function to be decorated.

        Returns:
            function: The wrapped function with logging.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.info(f'Executing {func.__name__} with args: {args}')
            result = func(*args, **kwargs)
            self.logger.info(f'Finished {func.__name__} with result: {result}')
            return result
        return wrapper

    def generate_host_cmd_log(self, host, command_name):
        """
        Generate log file path for a specific host and command.

        Args:
            host (str): The host name or IP address.
            command_name (str): The name of the command.

        Returns:
            str: The generated log file path.
        """
        safe_host = host.replace('.', '-')
        timestamp = self.format_datetime(datetime.now())
        return f'logs/hosts/{safe_host}/{command_name}_{timestamp}.log'
    
    def generate_activity_log(self):
        """
        Generate log file for a activities and configure logger.

        Returns:
            str: The generated log file path.
        """
        log_file_path = f'logs/activity.log'

        check_and_create_directory(os.path.dirname(log_file_path))

        # Configure the logger
        handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5  # Keep up to 5 backup files
        )

        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        # Configure the logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

        print(f'Logging to {log_file_path}')
        return log_file_path

    def write_output(self, file_path, text):
        """
        Write text to the specified file.

        Args:
            file_path (str): The path of the file to write to.
            text (str): The text to write to the file.
        """
        check_and_create_directory(os.path.dirname(file_path))
        with open(file_path, 'w', newline='') as f:
            f.write(text)

    def format_datetime(self, timestamp):
        """
        Format all datetime objects to a set format. This provides consistency in
        the application. All datetime transformations should use this.

        Args:
            timestamp (datetime): The datetime object to format.

        Returns:
            str: The formatted datetime string.
        """
        return timestamp.strftime('%Y-%m-%d_%H-%M-%S')


def class_logger(logger_instance):
    """
    Class decorator to log all methods of a class using the provided logger instance.

    Args:
        logger_instance (Logger): The Logger instance to use for logging.

    Returns:
        function: The class decorator.
    """
    def class_decorator(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value) and not attr_name.startswith('__'):
                setattr(cls, attr_name, logger_instance.log_action(attr_value))
        return cls
    return class_decorator