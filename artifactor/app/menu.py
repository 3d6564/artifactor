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
          self.run_cmd = Run(self.env_manager, 
                         self.cmd_manager,
                         self.cmd_executor,
                         self.host_manager)
          self.command_map = self._generate_command_map()

          configure_fetchers = {
            'configure': fetch_subclasses(Configure),
            'hosts': fetch_nested_submethods(Configure, Hosts),
            'commands': fetch_nested_submethods(Configure, Commands),
            'environment': fetch_nested_submethods(Configure, Environment),
          }
          setattr(self, 'complete_configure', create_complete_methods('configure', configure_fetchers).__get__(self))

          run_fetchers = {
            'run': fetch_nested_submethods(Run, self.run_cmd)
          }
          setattr(self, 'complete_run', create_complete_methods('run', run_fetchers).__get__(self))

     def _generate_command_map(self):
          """dynamically generate the base command map"""
          command_map = {}
          for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
               if name.startswith('do_'):
                    command_name = name[3:]  # remove 'do_' prefix
                    command_map[command_name] = method

          return command_map

     def do_run(self, args):
          """run a command on hosts loaded to application"""
          args = args.split()
          if not args or args[0] == 'help':
              # print(type(run_cmd))
               self.print_dynamic_help(Run, self.run_cmd)
               return
          
          if args[0] and self.host_manager.hosts:
               exit_status = self.run_cmd.onecmd(args[0])
          elif self.host_manager.hosts:
               exit_status = self.run_cmd.cmdloop()
          else:
               print("\033[1;31mNo hosts available. Please add hosts first.\033[0m")

          if exit_status == 2:
               self.exit_code = 2
               return True

     def do_configure(self, args):
          """configure additional settings in application"""
          args = args.split()
          if not args or args[0] == 'help':
               self.print_dynamic_help(Configure)
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

     def do_ping(self, args):
          """run ping scan"""
          args = args.split(',')
          if not args or args[0] == 'help':
               return
          hosts = [item.strip() for item in args if item.strip()]
          hosts = hosts or self.host_manager.hosts
          for host in hosts:
               print(f"{host}: {self.cmd_executor.ping_ttl(self.env_manager, host)}")

     def do_quit(self, arg):
          """exit the application"""
          self.exit_code = 2
          return True

     def print_dynamic_help(self, cls, args):
          """dynamically generate and print help information with descriptions from docstrings"""
          name =  cls.__name__.lower()
          description = inspect.getdoc(cls) if cls else "No description available"

          print(f"\n{name} - {description}")
          print("\nUsage:")
          print(f"  {name} <subcommand>")

          if args:
               methods = [
                    method_name for method_name in dir(args)
                    if method_name.startswith('do_')
               ]
          else:
               subcls = cls.__subclasses__()
          if methods:
               print("\nSubcommands:")
               for method_name in methods:
                    method = getattr(args, method_name)
                    subcommand = method_name[3:]
                    subcommand_description = inspect.getdoc(method) or "No description available"
                    print(f"  {subcommand:<20}     {subcommand_description}")
          elif subcls:
               print("\nSubcommands:")
               for method in subcls:
                    print(method)
                    subcommand = method.__name__.lower()
                    subcommand_description = inspect.getdoc(method) or "No description available"
                    print(f"  {subcommand:<20}     {subcommand_description}")


     def completenames(self, text, *ignored):
          """override command complete with a trailing space"""
          text_parts = text.split()

          if not text_parts:
               # if no text, suggest all top level commands
               return sorted({cmd.split()[0] + ' ' for cmd in self.command_map if ' ' not in cmd})
          
          if len(text_parts) == 1:
               # top level command completion
               return sorted({cmd.split()[0] + ' ' for cmd in self.command_map if ' ' not in cmd and cmd.startswith(text_parts[0])})


class Configure():
     """configure submenu"""

class Hosts(Configure):
     """modify hosts"""
     def __init__(self, app, args):
          self.host_manager = app.host_manager
          self.command_map = dir(Hosts)
          subcmd = getattr(self, args[0])
          if len(args) > 1:
               subcmd(args[1])
          else:
               try:
                    subcmd()
               except:
                    print('Command takes an argument')

     def add(self, args):
          """add a host to the host file"""
          args = args.split()
          if not args or args[0] == 'help':
               return
          if not any(args[0] in host for host in self.host_manager.hosts):
               if ip_check(args[0]):
                    if self.host_manager.add_host(args[0]):
                         print(f"Host {args[0]} added. Hosts saved to {self.host_manager.hosts_file}.")
               else:
                    print(f"Host {args[0]} was not a valid ip address.")
          else:
               print(f"Host {args[0]} is already in the list.")

     def load(self, args):
          """load hosts from file"""
          args = args.split()
          if not args or args[0] == 'help':
               return
          self.host_manager.hosts = self.host_manager.load_hosts(args[0])
          print(f"Hosts loaded from file: {args[0]}")

     def show(self, args):
          """show hosts loaded"""
          print(self.host_manager.hosts)

     def help(self):
          """print help"""
          print("\nSubcommands:")
          for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
               if name not in set(dir(Configure)):
                    print(f"  {name:<20}     {inspect.getdoc(method)}")

class Commands(Configure):
     """place to organize the commands parser commands"""  

     def __init__(self, app, args):
          self.cmd_manager = app.cmd_manager
          self.command_map = dir(Commands)
          subcmd = getattr(self, args[0])
          if len(args) > 1:
               subcmd(args[1])
          else:
               try:
                    subcmd()
               except:
                    print('Command takes an argument')

     def add_command(self,args ):
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
     
     def help(self):
          """print help"""
          print("\nSubcommands:")
          for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
               if name not in set(dir(Configure)):
                    print(f"  {name:<20}     {inspect.getdoc(method)}")

class Environment(Configure):
     """place to organize environment commands for parser"""

     def __init__(self, app, args):
          self.env_manager = app.env_manager
          self.command_map = dir(Environment)
          subcmd = getattr(self, args[0])
          if len(args) > 1:
               subcmd(args[1])
          else:
               try:
                    subcmd()
               except Exception as E:
                    print(E)
                    print('Command takes an argument')

     def set(self, var, val):
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

     def show(self, args):
          'Show existing environment configuration: show'
          print("\n\033[1;31mconfiguration:\033[0m")
          for var in self.env_manager.env_vars:
               print(f"    {var}={self.env_manager.get_env_var(var)}")
          print() 

     def help(self, args):
          """print help"""
          print("\nSubcommands:")
          for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
               if name not in set(dir(Configure)):
                    print(f"  {name:<20}     {inspect.getdoc(method)}")

class Run(Cmd):
     """run commands in application"""
     def __init__(self, env_manager, cmd_manager, cmd_executor, host_manager):
          'Run a command on hosts loaded to application: run [<command_name>]'
          super().__init__()
          self.env_manager = env_manager
          self.host_manager = host_manager
          self.cmd_manager = cmd_manager
          self.cmd_executor = cmd_executor
          self.selected_command = None
          self.commands = list(self.cmd_manager.commands.keys())
          self._create_dynamic_commands()
          ##print(self.__dict__.items())

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
               dynamic_method.__doc__ = f'{description}'
               return dynamic_method

          for command in self.commands:
               description = self.cmd_manager.commands[command].get('description', 'No description available')
               method = create_method(command, description)
               setattr(self, method.__name__, types.MethodType(method, self))

     """
     Currently not used
     def do_list(self, arg):
          'List commands to run: list'
          commands = list(self.cmd_manager.commands.keys())
          if commands:
               for idx, command in enumerate(commands, 1):
                    print(f"{command}")
          else:
               print("No commands available.")
               return
     """