import types
import inspect
from cmd import Cmd
from config import CommandManager
from utils import ExitApplication, Logger, class_logger, common_help, ip_check


logger_instance = Logger()

def dynamic_complete(self, text, line, begidx, endidx, command_name, subcommand_fetchers):
     """dynamic method for tab completion of subcommands and nested subcommands."""
     
     try:
          remaining_text = line[len(command_name):].strip()
     except Exception:
          return []

     # fetch possible primary subcommands
     possible_matches = subcommand_fetchers.get(command_name)

     # if remaining_text is empty, suggest primary subcommands
     if not remaining_text:
          return [sc + ' ' for sc in possible_matches]

     # split remaining_text to handle subcommands and nested subcommands
     split_text = remaining_text.split(maxsplit=1)
     primary_subcommand = split_text[0]
     remaining_subtext = split_text[1] if len(split_text) > 1 else ''
     
     # check matching subcommand and not only a space typed
     if ' ' not in remaining_text and primary_subcommand not in possible_matches:
          filtered_matches = [sc for sc in possible_matches if sc.startswith(remaining_text)]
          return [sc + ' ' for sc in filtered_matches]

     # get nested subcommands if subcommand fully typed
     if primary_subcommand in subcommand_fetchers:
          subcommands = subcommand_fetchers[primary_subcommand]
          return [sc for sc in subcommands if sc.startswith(remaining_subtext)]

     return []

def create_complete_methods(command_name, subcommand_fetchers):
     """Create a complete_<command_name> method dynamically with support for nested subcommands."""
     def complete_method(self, text, line, begidx, endidx):
          return dynamic_complete(self, text, line, begidx, endidx, command_name, subcommand_fetchers)
     return complete_method

def fetch_subclasses(cls):
    # Primary subcommands under 'configure'
    subcommands = [subclass.__name__.lower() for subclass in cls.__subclasses__()]
    return subcommands + ['help']

def fetch_nested_submethods(cls, sub_cls):
    # Nested subcommands under 'configure hosts'
    subcommands = list(set(dir(sub_cls)) - set(dir(cls)))
    return subcommands + ['help']

@class_logger(logger_instance)
class MainCmd(Cmd):
     prompt = 'artc> '
     intro = '\ntype ? or help to list options'
     
     def __init__(self, env_manager, host_manager, cmd_manager, cmd_executor):
          super().__init__()
          self.env_manager = env_manager
          self.host_manager = host_manager
          self.cmd_manager = cmd_manager
          self.cmd_executor = cmd_executor
          self.configure_handler = Configure()
          self.command_map = self._generate_command_map()

          configure_fetchers = {
            'configure': fetch_subclasses(Configure),
            'hosts': fetch_nested_submethods(Configure, Hosts),
            'commands': fetch_nested_submethods(Configure, Commands),
            'environment': fetch_nested_submethods(Configure, Environment),
          }
          setattr(self, 'complete_configure', create_complete_methods('configure', configure_fetchers).__get__(self))

     @staticmethod
     def _get_functions_static(cls):
          """Static version of _get_functions to be used within static context."""
          methods = []
          for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
               if not name.startswith('_'):
                    methods.append(name)
          return methods

     def _generate_command_map(self):
          """dynamically generate the command map"""
          command_map = {}
          for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
               if name.startswith('do_'):
                    command_name = name[3:]  # remove 'do_' prefix
                    command_map[command_name] = method

          return command_map

     def do_run(self, arg):
          """run a command on hosts loaded to application""" 
          self.run_parser.add_argument('c', type=str, choices=list(self.cmd_manager.commands.keys()))
          run_cmd = Run(self.env_manager, 
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

     def do_configure(self, args):
          """configure additional settings in application"""
          args = args.split()
          if not args or args[0] == 'help':
               self.print_dynamic_help('configure', ['hosts', 'commands', 'environment'])
               return
          
          subcommand = args[0]

          if subcommand == "hosts":
               Hosts(self, args[1:])
          elif subcommand == "commands":
               Commands(self, args[1:])
          elif subcommand == 'environment':
               Environment(self, args[1:])
          else:
               print(f"Unknown subcommand: {subcommand}")

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

     def print_dynamic_help(self, command_path, subcommands):
          """dynamically generate and print help information with descriptions from docstrings"""
          current_method = self.command_map.get(command_path)
          description = inspect.getdoc(current_method) if current_method else "No description available"

          print(f"{command_path} - {description}")
          print("Usage:")
          print(f"  {command_path} <subcommand>")
          if subcommands:
               print("Subcommands:")
               for subcommand in subcommands:
                    subcommand_path = f"{command_path} {subcommand}"
                    subcommand_method = self.command_map.get(subcommand_path)
                    subcommand_description = inspect.getdoc(subcommand_method) or "No description available"
                    print(f"  {subcommand} - {subcommand_description}")
          print("  help - Show this message")

     def completenames(self, text, *ignored):
          """Override to complete command names with a trailing space."""
          matches = []
          text_parts = text.split()

          if len(text_parts) == 1:
               # Top-level command completion: Suggest only commands without spaces
               for cmd in self.command_map:
                    if ' ' not in cmd and cmd.startswith(text_parts[0]):
                         matches.append(cmd.split()[0] + ' ')
          elif len(text_parts) > 1:
               # Handle subcommands and nested commands after a top-level command
               current_path = ' '.join(text_parts[:-1])
               for cmd in self.command_map:
                    if cmd.startswith(current_path) and len(cmd.split()) == len(text_parts):
                         next_part = cmd.split()[len(text_parts) - 1]
                         if next_part.startswith(text_parts[-1]):
                              matches.append(next_part + ' ')

          # If nothing is typed, suggest all top-level commands
          if not text:
               for cmd in self.command_map:
                    if ' ' not in cmd:
                         matches.append(cmd.split()[0] + ' ')

          return list(sorted(set(matches)))  # Remove duplicates
     
     def _get_functions(self, cls):
               methods = []
               for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
                    if not name.startswith('_'):
                         methods.append(name)
               return methods

class Configure():
     """configure submenu"""

     def do_commands(self, args):
          """modify commands"""
          if args.arg == 'add':
               Commands().add_command()
          elif args.arg == 'load':
               if args.f:
                    Commands().load_commands(args.f)
               else:
                    self.cmd_manager.load_commands()
          elif args.arg == 'save':
               Commands().save_commands()
          elif args.arg == 'copy':
               Commands().copy_command(args.s, args.d, args.c)
          elif args.arg == 'show':
               print(list(self.cmd_manager.commands.keys()))

     def environment(self, args):
          """modify environment"""
          if args.arg == 'show':
               Environment().show_environment()
          elif args.arg == 'set':
               Environment().set_environment(args.n, args.v)

     def get_nested_commands(self):
          """Return the list of nested command names."""
          return list(Configure.hosts_args)

class Hosts(Configure):
     """modify hosts"""
     def __init__(self, app, args):
          self.host_manager = app.host_manager
          subcmd = getattr(self, args[0])
          if len(args) > 1:
               subcmd(args[1])
          else:
               try:
                    subcmd()
               except:
                    print('Command takes an argument')

     def add(self, arg):
          """add a host to the host file"""
          if not any(arg in host for host in self.host_manager.hosts):
               if ip_check(arg):
                    if self.host_manager.add_host(arg):
                         print(f"Host {arg} added. Hosts saved to {self.host_manager.hosts_file}.")
               else:
                    print(f"Host {arg} was not a valid ip address.")
          else:
               print(f"Host {arg} is already in the list.")

     def load(self, arg):
          """load hosts from file"""
          self.host_manager.hosts = self.host_manager.load_hosts(arg)
          print(f"Hosts loaded from file: {arg}")

     def show(self):
          """show hosts loaded"""
          print(self.host_manager.hosts)

     def help(self):
          """print help"""
          for name, method in self.command_map.items():
               print(f"{name} - {inspect.getdoc(method)}")


class Commands(Configure):
     """place to organize the commands parser commands"""  

     def __init__(self, app, args):
          self.cmd_manager = app.cmd_manager
          subcmd = getattr(self, args[0])
          if len(args) > 1:
               subcmd(args[1])
          else:
               try:
                    subcmd()
               except:
                    print('Command takes an argument')

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

     def show_commands(self, arg):
          """show commands"""
          print(list(self.cmd_manager.commands.keys()))

class Environment(Configure):
     """place to organize environment commands for parser"""

     def __init__(self, app, args):
          self.env_manager = app.env_manager
          subcmd = getattr(self, args[0])
          if len(args) > 1:
               subcmd(args[1])
          else:
               try:
                    subcmd()
               except:
                    print('Command takes an argument')

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
