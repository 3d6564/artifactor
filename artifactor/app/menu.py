import types
from cmd import Cmd
from config import CommandManager
from utils import ExitApplication, Logger, class_logger, common_help
import cmd2

logger_instance = Logger()


@class_logger(logger_instance)
class MainCmd(cmd2.Cmd):
     prompt = 'artc> '
     intro = '\ntype ? or help to list options'

     # Parsers
     configure_parser = cmd2.Cmd2ArgumentParser()
     configure_subparser = configure_parser.add_subparsers(title='subcommands', help='subcommand help')

     run_parser = cmd2.Cmd2ArgumentParser()

     parser_hosts = configure_subparser.add_parser('hosts', help='hosts help')
     parser_hosts.add_argument('t', type=str, help='add, load')
     parser_hosts.add_argument('-i', type=str, help='ip address')
     parser_hosts.add_argument('-f', type=str, help='file name')

     parser_commands = configure_subparser.add_parser('commands', help='commands help', 
                                                  epilog='The copy command is intended for copying from a distro ' +
                                                  'where the source and destination command would match.')
     parser_commands.add_argument('t', type=str, help='add, copy, load, save, show')
     parser_commands.add_argument('-s', type=str, help='source distro for copy')
     parser_commands.add_argument('-d', type=str, help='destination distro for copy')
     parser_commands.add_argument('-c', type=str, help='command for copy')
     parser_commands.add_argument('-f', type=str, help='file name')

     parser_env = configure_subparser.add_parser('env', help='environment help')
     parser_env.add_argument('t', type=str, help='set, show')
     parser_env.add_argument('-n', type=str, help='variable name to set')
     parser_env.add_argument('-v', type=str, help='value to set')   
     
     def __init__(self, env_manager, host_manager, cmd_manager, cmd_executor):
          super().__init__()
          self.env_manager = env_manager
          self.host_manager = host_manager
          self.cmd_manager = cmd_manager
          self.cmd_executor = cmd_executor  

          self.hidden_commands = ['alias','macro', '_relative_run_script', 'eof']
          del cmd2.Cmd.do_edit
          del cmd2.Cmd.do_run_pyscript
          del cmd2.Cmd.do_run_script
          del cmd2.Cmd.do_set
          del cmd2.Cmd.do_shell
          del cmd2.Cmd.do_shortcuts

     def hosts(self, args):
          """modify hosts"""
          if args.t == 'add':
               if self.host_manager.add_host(args.i):
                    print(f"Host {args.i} added. Hosts saved to {self.host_manager.hosts_file}.")
               else:
                    print(f"Host {args.i} is already in the list.")
          elif args.t == 'load':
               Host().load_hosts(args.f)
               print(f"Hosts loaded from file: {args.f}")

     def commands(self, args):
          """modify commands"""
          if args.t == 'add':
               Commands().add_command()
          elif args.t == 'load':
               if args.f:
                    Commands().load_commands(args.f)
               else:
                    self.cmd_manager.load_commands()
          elif args.t == 'save':
               Commands().save_commands()
          elif args.t == 'copy':
               Commands().copy_command(args.s, args.d, args.c)

     def environment(self, args):
          """modify environment"""
          if args.t == 'show':
               Environment().show_environment()
          elif args.t == 'set':
               Environment().set_environment(args.n, args.v)

     @cmd2.with_argparser(run_parser)
     def do_run(self, arg):
          """run a command on hosts loaded to application""" 
          self.run_parser.add_argument('c', type=str, choices=list(self.cmd_manager.commands.keys()))
          run_cmd = RunCmd(self.env_manager, 
                         self.cmd_manager,
                         self.cmd_executor,
                         self.host_manager,
                         arg)
          if arg and self.host_manager.hosts:
               exit_status = run_cmd.onecmd(arg)
          elif self.host_manager.hosts:
               exit_status = run_cmd.cmdloop()
          else:
               print("\033[1;31mNo hosts available. Please add hosts first.\033[0m")

          if exit_status == 2:
               self.exit_code = 2
               return True

     parser_hosts.set_defaults(func=hosts)
     parser_commands.set_defaults(func=commands)
     parser_env.set_defaults(func=environment)

     @cmd2.with_argparser(configure_parser)
     def do_configure(self, args):
          """configure additional settings in application"""
          func = getattr(args, 'func', None)
          if func is not None:
               # Call whatever subcommand function was selected
               func(self, args)
          else:
               # No subcommand was provided, so call help
               self.do_help('configure')

     def do_ping(self, arg):
          """run ping scan"""
          hosts = [item.strip() for item in arg.split(',') if item.strip()]
          hosts = hosts or self.host_manager.hosts
          for host in hosts:
               print(f"{host}: {self.cmd_executor.ping_ttl(self.env_manager, host)}")

     def do_quit(self, arg):
          """exit the application"""
          self.exit_code = 2
          return True

class Commands():
     """place to organize the commands parser commands"""  

     def add_command(self):
          """add or update a command with a series of menus"""

          command_name =  input("Enter the command name (no spaces) or exit: ").strip().lower()
          if command_name == 'exit' or not command_name:
               return
          
          description = input("Enter the command description: ").strip()
          if not description:
               print("Description cannot be empty. Please provide a valid description.")
               return
          
          commands = {}
          while True:
               distro = input("\033[32mArtifactor will look in the /etc/os-release ID= field for the os. \n"
                              "Common entries for this are ubuntu, debian, fedora, centos, rhel, and arch. \n"
                              "Enter the distribution name (or type 'done' to finish): \033[0m").strip().lower()
               if distro == 'done' or not distro:
                    break
               if distro in commands:
                    print(f"\033[1;32mDistribution '{distro}' already added to this command.\033[0m")
                    continue
               if self.cmd_manager.distribution_exists(distro):
                    print(f"\033[1;32mDistribution '{distro}' already exists in the commands file.\033[0m")
               if not self.cmd_manager.distribution_exists(distro):
                    confirm = input(f"\033[1;31mDistribution '{distro}' is a new distribution. Is that correct? (y/n): \033[0m").lower()
                    if confirm == 'n':
                         continue

               command = input(f"Enter the command for {distro}: ")
               use_sudo = input(f"Does this command require sudo? (yes/no): ").strip().lower() == "yes"
               confirm = input(f"\033[1;31mYou entered '{distro}' with the command '{command}' with the command name '{command_name}'.\n"
                              "Is that correct? (y/n):\033[0m ").lower()
               if confirm.lower() in ['yes', 'y']:
                    if command == 'null' or command == '':
                         command = None
                    commands[distro] = {"cmd": command, "sudo": use_sudo}

                    print(f"\033[1;30mCommand '{command_name}' stored for '{distro}' with the command '{command}'. It will be written\n"
                         "to the file when 'done'.\033[0m")

          if commands:
               command_entry = {"description": description}
               command_entry.update(commands)
               self.cmd_manager.modify_commands(command_name, command_entry)
               print(f"Command '{command_name}' added/updated successfully.")
               return
          else:
               print("Invalid option. No command added.")
               return

     def copy_command(self, src, dest, cmd):
          """copy a command from a distribution"""
          while True:
               if not cmd:
                    cmd = input("Enter the command name you want to copy (or type 'back' to return): ")
                    if cmd.lower() == 'back':
                         break
                    if cmd not in self.cmd_manager.commands:
                         print(f"Command '{cmd}' does not exist.")
                         continue
               if not src:
                    src = input("Enter the source distribution: ")
                    if src not in self.cmd_manager.commands[cmd]:
                         print(f"Distribution '{src}' does not exist for command '{cmd}'.")
                         continue
               if not dest:
                    dest = input("Enter the destination distribution: ")

               self.cmd_manager.commands[cmd][dest] = self.cmd_manager.commands[cmd][src]
               self.cmd_manager.save_commands()
               print(f"Command '{cmd}' copied from '{src}' to '{dest}' successfully.")
               break

     def load_commands(self, arg):
          """commands subcommand for load command"""
          self.cmd_manager.commands_file = arg
          self.cmd_manager.commands = self.cmd_manager.load_commands()
          print(f"Commands loaded from {self.cmd_manager.commands_file}")

     def save_commands(self, arg):
          """save commands"""
          self.cmd_manager.save_commands()
          print("Commands saved.")

class Environment():
     """place to organize environment commands for parser"""

     def set_environment(self, var, val):
          """set environment variables"""
          var_digits = ['PING_COUNT','PING_TIMEOUT']
          if var in var_digits:
               if val.isdigit():
                    print(f'old value: {self.env_manager.get_env_var(var)}')
                    self.env_manager.set_env_var(var, val)
                    print(f'new value: {self.env_manager.get_env_var(var)}')
               else:
                    print("Invalid input. Please enter a number.")
          else:
               self.env_manager.set_env_var(var, val)

     def show_environment(self):
          'Show existing environment configuration: show'
          print("\n\033[1;31mconfiguration:\033[0m")
          for var in self.env_manager.env_vars:
               print(f"    {var}={self.env_manager.get_env_var(var)}")
          print() 

class Host():
     """place to organizer host commands for parser"""

     def load_hosts(self, arg):
          """hosts subcommand for load command"""
          self.host_manager.hosts_file = arg
          self.host_manager.hosts = self.host_manager.load_hosts()
          print(f"Hosts loaded from {self.host_manager.hosts_file}: {self.host_manager.hosts}")

class Run():
     """run commands in application"""

     def __init__(self):
          'Run a command on hosts loaded to application: run [<command_name>]'
          super().__init__()
          self.selected_command = None
          self.commands = list(self.cmd_manager.commands.keys())
          self._create_dynamic_commands()

     def _create_dynamic_commands(self):
          'This generates a dynamic list of commands to run: none'
          def create_method(cmd, description):
            def dynamic_method(self, arg):
                'Dynamically generated method for each command'
                self.selected_command = cmd
                self.cmd_executor.run_command(
                    self.env_manager,
                    self.selected_command,
                    self.host_manager.hosts
                )
                return True
            dynamic_method.__name__ = f'do_{cmd}'
            dynamic_method.__doc__ = f'{cmd}: {description}'
            return dynamic_method

          for command in self.commands:
               description = self.cmd_manager.commands[command].get('description', 'No description available')
               method = create_method(command, description)
               setattr(self, method.__name__, types.MethodType(method, self))

     def do_list(self, arg):
          'List commands to run: list'
          commands = list(self.cmd_manager.commands.keys())
          if commands:
               for idx, command in enumerate(commands, 1):
                    print(f"{command}")
          else:
               print("No commands available.")
               return
