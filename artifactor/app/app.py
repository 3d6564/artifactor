from cmd import Cmd
from .menu import ConfigureCmd, RunCmd
from config import EnvManager, HostManager, CommandManager, CommandExecutor
from utils import ExitApplication, common_help


class Artifactor(Cmd):
    prompt = 'artc> '
    intro = '\ntype ? or help to list options'

    def __init__(self):
        super().__init__()
        self.initialize_environment()

    def initialize_environment(self):
        print("\nInitializing environment...\n")
        self.env_manager = EnvManager()
        self.host_manager = HostManager()
        self.cmd_manager = CommandManager()
        self.cmd_executor = CommandExecutor()
        self.env_manager.initialize_env()
        if self.host_manager.hosts:
            print("\033[1;32mhosts have been initialized.\033[0m")
        if self.cmd_manager.commands:
            print("\033[1;32mcommands have been initialized.\033[0m")

    def do_show(self, arg):
        'Show existing environment configuration: show'
        print("\n\033[1;31mconfiguration:\033[0m")
        for var in self.env_manager.env_vars:
            print(f"    {var}={self.env_manager.get_env_var(var)}")
        print()

    def do_load(self, arg):
        'Load hosts or commands from the default or a custom file: load (hosts | commands) [<path/to/file>]'
        type = arg.strip() if arg else ''
        options = arg.split(' ', 1)
        if type.startswith('hosts'):
            self.host_manager.hosts_file = arg.split(' ', 1)[1].strip() if len(options) > 1 else self.host_manager.hosts_file
            self.host_manager.hosts = self.host_manager.load_hosts()
            print(f"Hosts loaded from {self.host_manager.hosts_file}: {self.host_manager.hosts}")
        elif type.startswith('commands'):
            self.cmd_manager.commands_file = arg.split(' ', 1)[1].strip() if len(options) > 1 else self.cmd_manager.commands_file
            self.cmd_manager.commands = self.cmd_manager.load_commands()
            print(f"Commands loaded from {self.cmd_manager.commands_file}")
        else:
            print("Invalid option. Nothing loaded.")

    def do_run(self, arg):
        'Run a command on hosts loaded to application: run [<command_name>]'     
        run_cmd = RunCmd(self.env_manager, 
                         self.cmd_manager,
                         self.cmd_executor,
                         self.host_manager,
                         arg)
        if arg and self.host_manager.hosts:
            run_cmd.onecmd(arg)
        elif self.host_manager.hosts:
            run_cmd.cmdloop()
        else:
            print("\033[1;31mNo hosts available. Please add hosts first.\033[0m")
            return

    def do_configure(self, arg):
        'Configure additional settings in application: configure [<sub-command>]'
        configure_cmd = ConfigureCmd(self.env_manager, 
                                     self.cmd_manager,
                                     self.host_manager,
                                     arg)
        if arg:
            configure_cmd.onecmd(arg)
        else:
            configure_cmd.cmdloop()

    def do_ping(self, arg):
        'Run ping scan: ping [<host>]'
        hosts = [item.strip() for item in arg.split(',') if item.strip()]
        hosts = hosts or self.host_manager.hosts
        for host in hosts:
            print(f"{host}: {self.cmd_manager.ping_ttl(host)}")

    def do_exit(self, arg):
        'Exit the application: exit'
        raise ExitApplication

    def do_help(self, arg):
        common_help(self, arg)