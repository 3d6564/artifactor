import json
from connectors import SSHClient
from .parallel_executor import ParallelExecutor
from config import EnvManager

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

    def detect_os(self, hosts, jumpbox, jumpbox_username, target_username, jumpbox_password=None, jumpbox_key_path=None, target_password=None, target_key_path=None):
        os_command = 'cat /etc/os-release'
        command_name = 'get_os'

        alternate_check = []

        print("Running os-release...")
        output = self.parallel_executor.execute_commands_in_parallel(self.ssh_client.run_command_on_host,
                                                                     os_command, 
                                                                     command_name,
                                                                     hosts, 
                                                                     jumpbox, 
                                                                     jumpbox_username=jumpbox_username, 
                                                                     target_username=target_username,
                                                                     jumpbox_key_path=jumpbox_key_path,
                                                                     target_key_path=target_key_path)
        for key, value in output.items():
            if 'ID=' in value:
                id_line = next(line for line in value.splitlines() if line.startswith('ID='))
                output[key] = id_line.split('=')[1].strip('"')
            else:
                alternate_check.append(key)
        if len(alternate_check) > 0:
            os_command = 'ver'  # Command to identify Windows OS
            print("Host might not be Linux... Running ver...")
            alternate_output = self.parallel_executor.execute_commands_in_parallel(self.ssh_client.run_command_on_host,
                                                                     os_command, 
                                                                     command_name,
                                                                     hosts, 
                                                                     jumpbox, 
                                                                     jumpbox_username=jumpbox_username, 
                                                                     target_username=target_username,
                                                                     jumpbox_key_path=jumpbox_key_path,
                                                                     target_key_path=target_key_path)
            for key, value in alternate_output.items():
                if 'Windows' in alternate_output:
                    output[key] = 'Windows'
        return output

    def run_command(self, command_name, hosts, jumpbox, jumpbox_username, target_username, jumpbox_key_path, target_key_path):
        self.commands = self.load_commands()
        print("Detecting OS's...")
        os_types = self.detect_os(hosts, 
                                  jumpbox, 
                                  jumpbox_username=jumpbox_username, 
                                  target_username=target_username, 
                                  jumpbox_key_path=jumpbox_key_path,
                                  target_key_path=target_key_path)
        print(os_types)

        for host, os_type in os_types.items():
            if os_type == 'unknown':
                print(f"Could not determine the OS of {host}. Skipping...")
                continue
            
            command = self.commands.get(command_name, {}).get(os_type)
            if command:
                if command.get("sudo"):
                    command["cmd"] = "sudo " + command["cmd"]
                results = self.parallel_executor.execute_commands_in_parallel(self.ssh_client.run_command_on_host, 
                                                                           command["cmd"], 
                                                                           command_name, 
                                                                           hosts, 
                                                                           jumpbox, 
                                                                           jumpbox_username=jumpbox_username, 
                                                                           target_username=target_username, 
                                                                           jumpbox_key_path=jumpbox_key_path, 
                                                                           target_key_path=target_key_path)
                print(results)
                return
            else:
                print(f"\033[1;31mCommand \"{command_name}\" not found for OS type \"{os_type}\"\033[0m")

        return None

    def modify_commands(self, command_name, commands):
        if command_name in self.commands:
            print(f"Updating existing command '{command_name}' with {commands}")
            self.commands[command_name].update(commands)
        else:
            print(f"Adding new command '{command_name}'")
            self.commands[command_name] = commands
        self.save_commands()

    def distribution_exists(self, distro):
        for command in self.commands.values():
            if distro in command:
                return True
        return False
    
