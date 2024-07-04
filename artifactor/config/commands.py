import json
import subprocess
import re
import shutil
from connectors import SSHClient
from .parallel_executor import ParallelExecutor


class CommandManager:

    def __init__(self, commands_file='commands.json'):
        self.commands_template = 'commands.json.template'
        self.ssh_client = SSHClient()
        self.commands_file = commands_file
        self.commands = self.load_commands()
        self.parallel_executor = ParallelExecutor()
        self.ping_count = 4
        self.ping_timeout = 4

    def load_commands(self):
        try:
            with open(self.commands_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"\033[1;33mCommands file {self.commands_file} does not exist... cloning template")
            try:
                shutil.copyfile(self.commands_template, self.commands_file)
                with open(self.commands_file, 'r') as f:
                    return json.load(f)
            except:
                print('\033[1;31mWarning: You do not have a commands file.')
                return {}

    def save_commands(self):
        with open(self.commands_file, 'w') as f:
            json.dump(self.commands, f, indent=4)

    def ping_ttl(self, host):
        try:
            # Execute ping command to get TTL
            result = subprocess.run(['ping', '-n', str(self.ping_count), '-w', str(self.ping_timeout), host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
                    return {'os_type': 'unknown', 'ttl': 'unknown'}
            else:
                return {'os_type': {result.stderr}, 'ttl': 'unknown'}
        except Exception as e:
            return f'An error occurred: {e}'

    def execute_commands(self, env_manager, host_dict):
        """Execute the specified command on all hosts in parallel."""
        output = self.parallel_executor.execute_commands_in_parallel(
            self.ssh_client.run_command_on_host,
            env_manager,
            host_dict
        )
        return output

    def detect_os(self, env_manager, hosts):
        """
        Detect the OS type of each host using ping TTL values and get_os function
        
        """
        print("Detecting OS's...")
        self.commands = self.load_commands()
        host_dict = {host: self.ping_ttl(host) for host in hosts}
        known_dict = {}
        unknown_dict = {}

        for host, values in host_dict.items():
            try:
                os_type = values["os_type"]
                values["command"] = self.commands.get('get_os').get(os_type).get("cmd")
                values["command_name"] = 'get_os'
                known_dict[host] = values
            except:
                os_type = 'unknown'
                values["os_type"] = os_type
                unknown_dict[host] = values

        output = self.execute_commands(env_manager, known_dict)
        
        for key, value in output.items():
            os_type = host_dict[key].get('os_type')
            if os_type == 'windows':
                print(f'Windows was detected {key} by ping ttl...')
                if 'OS Name:' in value:
                    id_line = next(line for line in value.splitlines() if line.startswith('OS Name:'))
                    if 'Microsoft Windows' in id_line:
                        host_dict[key]['os_type'] = 'win-winrm'
                    else:
                        host_dict[key]['os_type'] = id_line.split(':', 1)[1].strip()
                else:
                    print('OS Name not detected for the Windows host...')
            elif os_type == 'linux':
                print(f'Linux was detected on {key} by ping ttl...')
                if 'ID=' in value:
                    id_line = next(line for line in value.splitlines() if line.startswith('ID='))
                    host_dict[key]['os_type'] = id_line.split('=')[1].strip('"')
            else:
                print(f"Unknown OS detected for {key}.")
        return host_dict

    def run_command(self, env_manager, command_name, hosts):
        host_dict = self.detect_os(env_manager, hosts)

        for host, values in host_dict.items():
            try:
                values["command"] = self.commands.get(command_name).get(values["os_type"]).get("cmd")
            except:
                values["command"] = None
            values["command_name"] = command_name
            if values["command"] is None:
                print(f"\033[1;31m{command_name} not found for {values['os_type']} on host {host}.. \n" +
                    "Please add it to your commands file.\033[0m")

        for host, values in host_dict.items():
            if 'unknown' in values:
                print(f"Could not determine the OS of {host}. Skipping...")
                continue

        results = self.execute_commands(env_manager, host_dict)
        return results

    def distribution_exists(self, distro):
        for command in self.commands.values():
            if distro in command:
                return True
        return False
