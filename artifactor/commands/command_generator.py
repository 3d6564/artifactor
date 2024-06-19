import json
from connectors import SSHClient
from .parallel_executor import ParallelExecutor


class CommandGenerator:
    def __init__(self, commands_file='commands.json'):
        self.ssh_client = SSHClient()
        self.commands_file = commands_file
        self.commands = self.load_commands()
        self.parallel_executor = ParallelExecutor()

    def load_commands(self):
        try:
            with open(self.commands_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_commands(self):
        with open(self.commands_file, 'w') as f:
            json.dump(self.commands, f, indent=4)

    def run_command(self, command_name, hosts, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
        self.commands = self.load_commands()
        os_types = {host: self.ssh_client.detect_os(host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path) for host in hosts}
        
        for host, os_type in os_types.items():
            if os_type == 'unknown':
                print(f"Could not determine the OS of {host}. Skipping...")
                continue
            
            command = self.commands.get(command_name, {}).get(os_type)
            if command:
                return self.parallel_executor.execute_commands_in_parallel(self.ssh_client.run_command_on_host, command, command_name, hosts, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path, os_type)
            else:
                raise ValueError(f"Command '{command_name}' not found for OS type '{os_type}'")

    def modify_commands(self, command_name, linux_command, windows_command, debian_command=None, centos_command=None):
        if command_name in self.commands:
            print(f"Updating existing command '{command_name}'")
        else:
            print(f"Adding new command '{command_name}'")
        
        self.commands[command_name] = {
            "linux": linux_command,
            "debian": debian_command if debian_command else linux_command,
            "centos": centos_command if centos_command else linux_command,
            "windows": windows_command
        }
        self.save_commands()