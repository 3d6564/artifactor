import os
import logging
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
        # Replace periods with dashes for IP addresses
        safe_host = host.replace('.', '-')
        timestamp = self.format_datetime(datetime.now())
        return f'logs/hosts/{safe_host}/{command_name}_{timestamp}.log'
    
    def generate_activity_log(self):
        timestamp = self.format_datetime(datetime.now())
        log_file_path = f'logs/activity/{timestamp}.log'

        check_and_create_directory(os.path.dirname(log_file_path))

        # Configure the logger
        logging.basicConfig(
            filename=log_file_path,  # Log file path
            level=logging.INFO,  # Log level
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
            force=True
        )
        self.logger = logging.getLogger(__name__)

        print(f'Logging to {log_file_path}')
        return log_file_path

    def write_output(self, file_path, text):
        check_and_create_directory(os.path.dirname(file_path))
        with open(file_path, 'w', newline='') as f:
            f.write(text)

    def format_datetime(self, timestamp):
        return timestamp.strftime('%Y-%m-%d_%H-%M-%S')
    
'''
Class Logger
'''
def class_logger(logger_instance):
    def class_decorator(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value) and not attr_name.startswith('__'):
                setattr(cls, attr_name, logger_instance.log_action(attr_value))
        return cls
    return class_decorator