import os
from datetime import datetime

class Logger:
    def check_and_create_directory(self, directory):
            if not os.path.exists(directory):
                os.makedirs(directory)

    def generate_log_name(self, host, command_name):
        # Replace periods with dashes for IP addresses
        safe_host = host.replace('.', '-')
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        return f'logs/{safe_host}/{command_name}_{timestamp}.txt'

    def write_output(self, file_path, text):
        self.check_and_create_directory(os.path.dirname(file_path))
        with open(file_path, 'a') as f:
            f.write(text + '\n')