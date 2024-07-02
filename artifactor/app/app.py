import os
import json
import subprocess
from cmd import Cmd
from .menu import ConfigureCmd, RunMenuCmd
from config import EnvManager, HostManager
from commands import CommandGenerator


class Artifactor(Cmd):
    prompt = 'artc> '
    intro = '\nwelcome to artifactor. type ? to list options'

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
            print("\033[1;32mHosts have been initialized.\033[0m")
        if self.cmd_generator.commands:
            print("\033[1;32mCommands have been initialized.\033[0m")

    def add_host(self, arg):
        'Add a host: add <hostname_or_ip>'
        new_host = arg.strip()
        if self.host_manager.add_host(new_host):
            print(f"Host {arg} added. Hosts saved to {self.host_manager.hosts_file}.")
        else:
            print(f"Host {arg} is already in the list.")

    def do_load(self, arg):
        'Load hosts from file: load'
        self.host_manager.hosts_file = arg.strip() if arg else self.host_manager.hosts_file
        self.host_manager.hosts = self.host_manager.load_hosts()
        print(f"Hosts loaded from {self.host_manager.hosts_file}: {self.host_manager.hosts}")

    def do_run(self, arg):
        'Run commands on hosts: run [command_name]'       
        command_name = arg.strip() if arg else None

        if not command_name:
            commands_menu = RunMenuCmd(self.cmd_generator)
            commands_menu.cmdloop()
            command_name = commands_menu.selected_command

        if not command_name:
            print("No command selected.")
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
        # 'Configure settings: configure <setting> <value>'
        # if arg:
        #     setting, value = arg.split()
        #     if setting in self.settings:
        #         self.settings[setting] = int(value)
        #         print(f"Updated {setting} to {value}")
        #     else:
        #         print(f"Unknown setting {setting}")
        # else:
        #     configure_menu(self.env_manager)
        'Configure settings: configure'
        #configure_menu(self.env_manager)
        configure_cmd = ConfigureCmd(self.env_manager)
        configure_cmd.cmdloop()

    def do_ping(self, arg):
        'Run ping scan: ping [host]'
        hosts = [item.strip() for item in arg.split(',') if item.strip()]
        hosts = hosts or self.host_manager.hosts
        for host in hosts:
            print(f"{host}: {self.cmd_generator.ping_ttl(host)}")

    def do_exit(self, arg):
        'Exit the application: exit'
        return True

    def do_help(self, arg):
        'List available commands: help'
        Cmd.do_help(self, arg)