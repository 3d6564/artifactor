import json
import subprocess
import re
from connectors import SSHClient
from config import EnvManager
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

    def ping_ttl(self, host):
        try:
            # Execute ping command to get TTL
            result = subprocess.run(['ping', '-n', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                # Get TTL from response using regex
                ttl_search = re.search(r'TTL=(\d+)', result.stdout)
                if ttl_search:
                    ttl_value = int(ttl_search.group(1))
                    if ttl_value <= 64:
                        return {'os_type': 'linux', 'ttl': ttl_value}
                    elif ttl_value <= 128:
                        return {'os_type': 'windows', 'ttl': ttl_value}
                    else:
                        return {'os_type': 'unknown', 'ttl': ttl_value}
                else:
                    return 'TTL not found in the ping response.'
            else:
                return f'Ping failed: {result.stderr}'
        except Exception as e:
            return f'An error occurred: {e}'

    def detect_os(self, hosts, jumpbox, jumpbox_username, target_username, jumpbox_password=None, jumpbox_key_path=None, target_password=None, target_key_path=None):
        #command_name = 'get_os'
        host_dict = {}
        
        for host in hosts:
            host_dict[host] = self.ping_ttl(host)
        print(host_dict)

        for host in hosts:
            print(host)
            host["command_name"] = 'get_os'

        output = self.parallel_executor.execute_commands_in_parallel(self.ssh_client.run_command_on_host,
                                                                     host_dict,
                                                                     hosts, 
                                                                     jumpbox, 
                                                                     jumpbox_username=jumpbox_username, 
                                                                     target_username=target_username,
                                                                     jumpbox_key_path=jumpbox_key_path,
                                                                     target_key_path=target_key_path)

        for key, value in output.items():
            if 'Linux' in value:
                print(f'Linux was detected on {key} by ping ttl...')
                #os_command = self.commands.get(command_name)["linux"]
                # os_type = 'linux'
                # linux_output = self.parallel_executor.execute_commands_in_parallel(self.ssh_client.run_command_on_host,
                #                                                      os_command["cmd"], 
                #                                                      os_type,
                #                                                      command_name,
                #                                                      hosts, 
                #                                                      jumpbox, 
                #                                                      jumpbox_username=jumpbox_username, 
                #                                                      target_username=target_username,
                #                                                      jumpbox_key_path=jumpbox_key_path,
                #                                                      target_key_path=target_key_path)
                for key, value in output.items():
                    if 'ID=' in value:
                        id_line = next(line for line in value.splitlines() if line.startswith('ID='))
                        output[key] = id_line.split('=')[1].strip('"')
            elif 'Windows' in value:
                print(f'Windows was detected {key} by ping ttl...')
                #os_command = self.commands.get(command_name)["windows"]
                # os_type = 'windows'
                # win_output = self.parallel_executor.execute_commands_in_parallel(self.ssh_client.run_command_on_host,
                #                                                      os_command["cmd"],  
                #                                                      os_type,
                #                                                      command_name,
                #                                                      hosts, 
                #                                                      jumpbox, 
                #                                                      jumpbox_username=jumpbox_username, 
                #                                                      target_username=target_username,
                #                                                      jumpbox_key_path=jumpbox_key_path,
                #                                                      target_key_path=target_key_path)
                for key, value in output.items():
                    if 'OS Name:' in value:
                        id_line = next(line for line in value.splitlines() if line.startswith('OS Name:'))
                        if 'Microsoft Windows' in id_line:
                            output[key] = 'win-winrm'
                        else:
                            output[key] = id_line.split(':', 1)[1].strip()
                    else:
                        print('OS Name not detected for the Windows host...')
            else:
                print("Error....")

        # old logic
        """
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
        """
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
                return results
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
    