import os
import json
import subprocess
from cmd import Cmd
from .menu import ConfigureCmd, RunMenuCmd
from config import EnvManager, HostManager
from commands import CommandGenerator
from utils import ExitApplication


class Artifactor(Cmd):
    prompt = 'artc> '
    intro = '\ntype ? or help to list options'

    def __init__(self):
        super().__init__()

        print("\nInitializing environment...\n")

        # initialize environment
        self.env_manager = EnvManager()
        self.host_manager = HostManager()
        self.cmd_generator = CommandGenerator()
        self.initialize_environment()

    def initialize_environment(self):
        self.env_manager.initialize_env()
        if self.host_manager.hosts:
            print("\033[1;32mhosts have been initialized.\033[0m")
        if self.cmd_generator.commands:
            print("\033[1;32mcommands have been initialized.\033[0m")

    def do_show(self, arg):
        'Show existing environment configuration: show'
        print("\n\033[1;31mconfiguration:\033[0m")
        for var in self.env_manager.env_vars:
            print(f"    {var}={self.env_manager.get_env_var(var)}")
        print()

    def do_add(self, arg):
        'Add a host and save to host file: add <hostname_or_ip>'
        new_host = arg.strip()
        if new_host == "":
            print(f"Argument was empty.")
        elif self.host_manager.add_host(new_host):
            print(f"Host {arg} added. Hosts saved to {self.host_manager.hosts_file}.")
        else:
            print(f"Host {arg} is already in the list.")

    def do_load(self, arg):
        'Load hosts or commands from the default or a custom file: load (hosts | commands) [<path/to/file>]'
        type = arg.strip() if arg else ''
        options = arg.split(' ', 1)
        if type.startswith('hosts'):
            self.host_manager.hosts_file = arg.split(' ', 1)[1].strip() if len(options) > 1 else self.host_manager.hosts_file
            self.host_manager.hosts = self.host_manager.load_hosts()
            print(f"Hosts loaded from {self.host_manager.hosts_file}: {self.host_manager.hosts}")
        elif type.startswith('commands'):
            self.cmd_generator.commands_file = arg.split(' ', 1)[1].strip() if len(options) > 1 else self.cmd_generator.commands_file
            self.cmd_generator.commands = self.cmd_generator.load_commands()
            print(f"Commands loaded from {self.cmd_generator.commands_file}")
        else:
            print("Invalid option. Nothing loaded.")

    def do_run(self, arg):
        'Run a command on hosts loaded to application: run [<command_name>]'       
        command_name = arg.strip() if arg else None

        if not command_name:
            commands_menu = RunMenuCmd(self.cmd_generator)
            commands_menu.cmdloop()
            command_name = commands_menu.selected_command
            return

        if not self.host_manager.hosts:
            print("\033[1;31mNo hosts available. Please add hosts first.\033[0m")
            return

        if command_name:
            self.cmd_generator.run_command(
                command_name,
                self.host_manager.hosts,
                self.env_manager.env_vars.get('JUMPBOX'),
                self.env_manager.env_vars.get('JUMPBOX_USERNAME'),
                self.env_manager.env_vars.get('TARGET_USERNAME'),
                self.env_manager.env_vars.get('JUMPBOX_KEY'),
                self.env_manager.env_vars.get('TARGET_KEY')
            )

    def do_configure(self, arg):
        'Configure additional settings in application: configure [<sub-command>]'
        configure_cmd = ConfigureCmd(self.env_manager, self.cmd_generator, arg)
        configure_cmd.cmdloop()

    def do_ping(self, arg):
        'Run ping scan: ping [<host>]'
        hosts = [item.strip() for item in arg.split(',') if item.strip()]
        hosts = hosts or self.host_manager.hosts
        for host in hosts:
            print(f"{host}: {self.cmd_generator.ping_ttl(host)}")

    def do_exit(self, arg):
        'Exit the application: exit'
        raise ExitApplication

    def do_help(self, arg):
        'List available menu commands and usage: help [<arg>]'
        self.print_help(arg)

    def print_help(self, arg):
        'Print help information for all commands.'
        if arg:
            command_method = getattr(self, f'do_{arg}', None)
            help_info = command_method.__doc__ if command_method.__doc__ else ''
            description, command = help_info.split(':')
            command_parts = command.strip().split(' ', 1)
            if len(command_parts) == 1:
                command_parts.append('')
            command, command_options = command_parts
            print(f"\033[1;31m{arg}\033[0m\n\033[1;31mdescription:\033[0m {description}\n")
            print(f"\033[1;31musage:\033[0m {arg} {command_options}")
            print()
        else:
            print("\033[1;31musage:\033[0m <command> [<arg>]")
            print("\n\033[1;31mcommands:\033[0m")
            for attr in dir(self):
                if attr.startswith('do_'):
                    command_name = attr[3:]
                    command_method = getattr(self, attr)
                    help_info = command_method.__doc__ if command_method.__doc__ else ''
                    description, command = help_info.split(':')
                    print(f"    {command_name.ljust(15)} {description.lower()}")
            print()
