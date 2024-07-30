import json
import subprocess
import re
import shutil
from connectors import SSHClient
from .parallel_executor import ParallelExecutor


class CommandManager:

    def __init__(self, commands_file='commands.json'):
        """ Initialize commands for the application from file."""
        self.commands_template = 'commands.json.template'
        self.commands_file = commands_file
        self.commands = self.load_commands()

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

    def modify_commands(self, command_name, commands):
        if command_name in self.commands:
            print(f"Updating existing command '{command_name}' with {commands}")
            self.commands[command_name].update(commands)
        else:
            print(f"Adding new command '{command_name}'")
            self.commands[command_name] = commands
        self.save_commands()

    def distribution_exists(self, distro):
        """Check if distribution exists in commands"""
        return any(distro in command for command in self.commands.values())

class CommandExecutor:
    def __init__(self):
        self.ssh_client = SSHClient()
        self.cmd_manager = CommandManager()
        self.parallel_executor = ParallelExecutor()

    def execute_commands(self, env_manager, host_dict):
        """Execute the specified command on all hosts in parallel."""
        output = self.parallel_executor.execute_commands_in_parallel(
            self.ssh_client.run_command_on_host,
            env_manager,
            host_dict
        )
        return output
    
    def _get_initial_host_os(self, env_manager, hosts):
        """ Get initial os detection through ttl"""
        print("Detecting OS's...")
        self.commands = self.cmd_manager.load_commands()
        return {host: self.ping_ttl(env_manager, host) for host in hosts}
    
    def _get_host_command(self, host_dict, command_name):
        """ Get command for host from commands"""
        known_dict = {}
        unknown_dict = {}

        for host, values in host_dict.items():
            try:
                values["command"] = self.commands.get(command_name).get(values["os_type"]).get("cmd")
                values["sudo"] = self.commands.get(command_name).get(values["os_type"]).get("sudo")
                if values["command"] is None:
                    print(f"\033[1;31m{command_name} not found for {values['os_type']} on host {host}.. \n" +
                    "Please add it to your commands file.\033[0m")
                    unknown_dict[host] = values
                else:
                    known_dict[host] = values
            except:
                values["command"] = 'unknown'
                unknown_dict[host] = values
            values["command_name"] = command_name                

        return known_dict, unknown_dict

    def ping_ttl(self, env_manager, host):
        """ Executes basic ping command to get ttl from device"""
        ping_count = env_manager.get_env_var('PING_COUNT')
        ping_timeout = env_manager.get_env_var('PING_TIMEOUT')
        try:
            result = subprocess.run(['ping', '-n', str(ping_count), '-w', str(ping_timeout), host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                return {'os_type': result.stderr, 'ttl': 'unknown'}

            ttl_search = re.search(r'TTL=(\d+)', result.stdout)
            if ttl_search:
                ttl_value = int(ttl_search.group(1))
                if ttl_value <= 64:
                    os_type = 'linux'
                elif ttl_value <= 128:
                    os_type = 'windows'
                else:
                    os_type = 'unknown'
                print(f'{os_type.capitalize()} was detected on {host} by ping ttl...')
                return {'os_type': os_type, 'ttl': ttl_value}
            else:
                return {'os_type': 'unknown', 'ttl': 'unknown'}
        except Exception as e:
            return {'os_type': 'unknown', 'ttl': f'An error occurred: {e}'}

    def detect_os(self, env_manager, hosts):
        """
        Detect the OS type of each host using ping TTL values and get_os function
        """
        host_dict = self._get_initial_host_os(env_manager, hosts)
        known_dict, unknown_dict = self._get_host_command(host_dict, command_name='get_os')
        output = self.execute_commands(env_manager, known_dict)

        for key, value in output.items():
            os_type = host_dict[key].get('os_type')
            if os_type == 'windows':
                if 'OS Name:' in value:
                    id_line = next(line for line in value.splitlines() if line.startswith('OS Name:'))
                    if 'Microsoft Windows' in id_line:
                        host_dict[key]['os_type'] = 'win-winrm'
                    else:
                        host_dict[key]['os_type'] = id_line.split(':', 1)[1].strip()
            elif os_type == 'linux':
                if 'ID=' in value:
                    id_line = next(line for line in value.splitlines() if line.startswith('ID='))
                    host_dict[key]['os_type'] = id_line.split('=')[1].strip('"')
            else:
                print(f"Unknown OS detected for {key}.")
                host_dict[key]['os_type'] = 'unknown'
        return host_dict

    def run_command(self, env_manager, command_name, hosts):
        host_dict = self.detect_os(env_manager, hosts)

        known_dict, unknown_dict = self._get_host_command(host_dict, command_name)

        for host, values in unknown_dict.items():
            if 'unknown' in values:
                print(f"Could not determine the OS of {host}. Skipping...")
                continue

        results = self.execute_commands(env_manager, known_dict)
        return results
