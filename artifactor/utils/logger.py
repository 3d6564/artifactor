import os
import logging
from datetime import datetime
from functools import wraps

class Logger:
    def __init__(self):
        # Configure the logger
        self.logger = None
        self.generate_activity_log()

    def log_action(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.info(f'Executing {func.__name__} with args: {args} and kwargs: {kwargs}')
            result = func(*args, **kwargs)
            self.logger.info(f'Finished {func.__name__} with result: {result}')
            return result
        return wrapper

    def check_and_create_directory(self, directory):
            if not os.path.exists(directory):
                os.makedirs(directory)

    def generate_host_cmd_log(self, host, command_name):
        # Replace periods with dashes for IP addresses
        safe_host = host.replace('.', '-')
        timestamp = self.format_datetime(datetime.now())
        return f'logs/hosts/{safe_host}/{command_name}_{timestamp}.log'
    
    def generate_activity_log(self):
        timestamp = self.format_datetime(datetime.now())
        log_file_path = f'logs/activity/{timestamp}.log'

        self.check_and_create_directory(os.path.dirname(log_file_path))

        # Configure the logger
        logging.basicConfig(
            filename=log_file_path,  # Log file path
            level=logging.INFO,  # Log level
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Log format
        )

        self.logger = logging.getLogger(__name__)
        print(f'Logging to {log_file_path}')
        return log_file_path

    def write_output(self, file_path, text):
        self.check_and_create_directory(os.path.dirname(file_path))
        with open(file_path, 'w', newline='') as f:
            f.write(text)

    def format_datetime(self, timestamp):
        return timestamp.strftime('%Y-%m-%d_%H-%M-%S')