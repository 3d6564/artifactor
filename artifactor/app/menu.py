import pyfiglet
import random
import types
from cmd import Cmd
from termcolor import colored
from commands import CommandGenerator


def print_ascii_art():
     fonts = ['3-d','alligator','banner','big','bigchief',
              'catwalk','coinstak','colossal',
              'doom','linux','lockergnome',
              'nancyj','ntgreek','peaks','rowancap','shadow']
     random_font = random.choice(fonts)
     art = pyfiglet.figlet_format("artifactor", font=random_font).rstrip()
     art_color = 'green'
     art_line1 = 'A R T I F A C T O R'
     art_line2 = '3d6564'
     art_line3 = '3d6564@gmail.com'
     line1_color = 'yellow'
     line2_color = 'magenta'
     line3_color = 'red'
     print(colored(art, art_color) + '\n' + 
           colored(art_line1, line1_color) + '\n' +
           colored(art_line2, line2_color) + ' ' + 
           colored('(', line2_color) + 
           colored(art_line3, line3_color) + 
           colored(')', line2_color))

class ConfigureCmd(Cmd):
     prompt = 'artc-configure> '
     intro = 'Configuration menu. Type ? to list options'

     def __init__(self, env_manager):
          super().__init__()
          self.env_manager = env_manager
          #self.settings = settings
          self.command_generator = CommandGenerator()
          print(f"\nJumpbox Usage (current: {self.env_manager.get_env_var('USE_JUMPBOX')})")

     def do_modify_commands(self, arg):
          'Modify commands: modify_commands'
          modify_commands_menu(self.command_generator)

     def do_load_commands(self, arg):
          'Load commands: load_commands'
          self.command_generator.load_commands()
          print("Commands loaded.")

     def do_save_commands(self, arg):
          'Save commands: save_commands'
          self.command_generator.save_commands()
          print("Commands saved.")

     def do_jumpbox_usage(self, arg):
          'Modify Jumpbox usage: jumpbox_usage'
          self.env_manager.set_jumpbox_use()
          current_jumpbox_state = self.env_manager.get_or_prompt_env_var('USE_JUMPBOX', 'False')
          print(f"Jumpbox usage set to {current_jumpbox_state}")

     def do_ping_count(self, arg):
          'Change ping count: ping_count <value>'
          if arg.isdigit():
               self.settings['ping_count'] = int(arg)
               print(f"Ping count updated to {self.settings['ping_count']}")
          else:
               print("Invalid input. Please enter a number.")

     def do_ping_timeout(self, arg):
          'Change ping timeout: ping_timeout <value>'
          if arg.isdigit():
               self.settings['ping_timeout'] = int(arg)
               print(f"Ping timeout updated to {self.settings['ping_timeout']}")
          else:
               print("Invalid input. Please enter a number.")
     
     def do_back(self, arg):
          'Return to the main menu: back'
          return True
     
     def do_help(self, arg):
          'List available commands: help'
          Cmd.do_help(self, arg)

class RunMenuCmd(Cmd):
     prompt = 'artc-run> '
     intro = 'Run menu. Type ? to list options'

     def __init__(self, command_generator):
          super().__init__()
          self.command_generator = command_generator
          self.selected_command = None
          self.commands = list(self.command_generator.commands.keys())
          self._create_dynamic_commands()

     def _create_dynamic_commands(self):
          for command in self.commands:
               def dynamic_method(self, arg, cmd=command):
                    'Dynamically generated method for each command'
                    self.selected_command = cmd
                    return True  # Exit the loop after selection
               
               dynamic_method.__name__ = f'do_{command}'
               dynamic_method.__doc__ = f'Run the {command} command'
               setattr(self, dynamic_method.__name__, types.MethodType(dynamic_method, self))

     def do_list(self, arg):
          'List commands to run: list'
          commands = list(self.command_generator.commands.keys())
          if commands:
               for idx, command in enumerate(commands, 1):
                    print(f"{idx}. {command}")
          else:
               print("No commands available.")
               return

     def do_back(self, arg):
          'Return to the main menu: back'
          return True

     def do_help(self, arg):
          'List available commands: help'
          Cmd.do_help(self, arg)

class ModifyCommandsCmd(Cmd):
     prompt = 'artc-modify_commands> '
     intro = 'Modify Commands menu. Type ? to list options'

     def __init__(self, command_generator):
          super().__init__()
          self.command_generator = command_generator

     def do_add(self, arg):
          'Add or update a command: add'
          add_commands(self.command_generator)

     def do_copy(self, arg):
          'Copy a command from a distribution: copy'
          copy_command_menu(self.command_generator)

     def do_back(self, arg):
          'Return to the main menu: back'
          return True

     def do_help(self, arg):
          'List available commands: help'
          Cmd.do_help(self, arg)

def copy_command_menu(command_generator):
     while True:
          command_name = input("Enter the command name you want to copy (or type 'back' to return): ")
          if command_name.lower() == 'back':
               break
          if command_name not in command_generator.commands:
               print(f"Command '{command_name}' does not exist.")
               continue

          src_distro = input("Enter the source distribution: ")
          if src_distro not in command_generator.commands[command_name]:
               print(f"Distribution '{src_distro}' does not exist for command '{command_name}'.")
               continue

          dest_distro = input("Enter the destination distribution: ")
          command_generator.commands[command_name][dest_distro] = command_generator.commands[command_name][src_distro]
          command_generator.save_commands()
          print(f"Command '{command_name}' copied from '{src_distro}' to '{dest_distro}' successfully.")
          break
    
def modify_commands_menu(command_generator):
     modify_cmd = ModifyCommandsCmd(command_generator)
     modify_cmd.cmdloop()


def modify_command_menu():
     options = ["add or update a command",
                "clone command from a distribution",
                "back"
     ]
     
     print("\nadd or update command options:")
     for idx, option in enumerate(options, 1):
          print(f"{idx}. {option}")

     return input("Enter your choice: ")

def add_commands(command_generator):
     """
     This will go through a series of menus to allow the user to add commands for
     multiple distributions.
     """
     command_name =  input("Enter the command name (no spaces) or exit: ").strip().lower()
     if command_name == 'exit' or not command_name:
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
          if command_generator.distribution_exists(distro):
               print(f"\033[1;32mDistribution '{distro}' already exists in the commands file.\033[0m")
          if not command_generator.distribution_exists(distro):
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
          command_generator.modify_commands(command_name, commands)
          print(f"Command '{command_name}' added/updated successfully.")
          return
     else:
          print("Invalid option. No command added.")
          return


# def modify_commands_menu(command_generator):
#      while True:
#           choice = modify_command_menu()

#           if choice == '1':
#                add_commands(command_generator)
#           elif choice == '2':
#                copy_command_menu(command_generator)
#           elif choice == '3':
#                return
#           else:
#                print("\n\033[1;31mInvalid command choice, please try again.\033[0m")
