import pyfiglet
import random
from termcolor import colored
from commands import CommandGenerator


def print_ascii_art():
     fonts = ['3-d','alligator','banner','big','bigchief',
              'catwalk','coinstak','colossal',
              'doom','lean','linux','lockergnome',
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

def main_menu():
     options = [
        "Add a host",
        "Load hosts from file",
        "Run command on hosts",
        "Configure",
        "Run ping ttl test",
        "Exit"
     ]

     print("\nSelect an option:")
     for idx, option in enumerate(options, 1):
          print(f"{idx}. {option}")

     return input("Enter your choice: ")

def display_commands_menu():
     command_generator = CommandGenerator()
     commands = list(command_generator.commands.keys())

     while True:
          if commands:
               print("Select a command to run:")
               for idx, command in enumerate(commands, 1):
                    print(f"{idx}. {command}")
          else:
               print("No commands available.")
               
          print(f"{len(commands) + 1}. back")

          choice = input("Enter your choice: ")

          if choice.isdigit():
               choice = int(choice)
               if 1 <= choice <= len(commands):
                    return commands[choice - 1]
               elif choice == len(commands) + 1:
                    return None
          print("\n\033[1;31mInvalid command choice, please try again.\033[0m")

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


def modify_commands_menu(command_generator):
     while True:
          choice = modify_command_menu()

          if choice == '1':
               add_commands(command_generator)
          elif choice == '2':
               copy_command_menu(command_generator)
          elif choice == '3':
               return
          else:
               print("\n\033[1;31mInvalid command choice, please try again.\033[0m")

def configure_menu(env_manager):
     command_generator = CommandGenerator()
     current_jumpbox_state = env_manager.get_or_prompt_env_var('USE_JUMPBOX', 'False')

     while True:
          print("\nConfigure options:")
          print("1. Modify commands")
          print("2. Load commands")
          print("3. Save commands")
          print(f"4. Modify Jumpbox Usage (current: {current_jumpbox_state})")
          print("5. Back")

          choice = input("Enter your choice: ")

          if choice == '1':
               modify_commands_menu(command_generator)
          elif choice == '2':
               command_generator.load_commands()
          elif choice == '3':
               command_generator.save_commands()
          elif choice == '4':
               env_manager.set_jumpbox_use()
               current_jumpbox_state = env_manager.get_or_prompt_env_var('USE_JUMPBOX', 'False') # Update the current value
          elif choice == '5':
               return
          else:
               print("Invalid choice, please try again.")