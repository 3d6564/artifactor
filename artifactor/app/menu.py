import os
from commands import CommandGenerator
from config import EnvManager

def print_ascii_art():
    art = """\
    \033[1;32m
                   __  .__   ____              __                
    _____ ________/  |_|__| /  __\____   _____/  |__  _________
    \__  \\\_  __ \   __\  ||   __\\\__ \ /  ___\   __\/ _ \     \\
     / __ \|  | \/|  | |  ||  |   / __ \\  (___|  |  ( <_> )  |\/
    (____  /__|   |__| |__||__|  (____  /\__  /__|   \___/|__|   
         \/                           \/    \/                 
    \033[1;33m          A R T I F A C T O R
    \033[1;35m          3d6564 (\033[1;31m3d6564@gmail.com\033[1;35m)\033[0m
    """
    print(art)

def initialize_menu():
     env_manager = EnvManager()
     print("\nInitializing environment...\n")

     # Jumpbox
     if env_manager.get_env_var('USE_JUMPBOX') is None:
          env_manager.set_jumpbox_use()

     if env_manager.get_env_var('USE_JUMPBOX') == 'Y':
          jumpbox = env_manager.get_or_prompt_env_var('JUMPBOX', "Enter the hostname or ip of a jumpbox: ")
          jumpbox_username = env_manager.get_or_prompt_env_var('JUMPBOX_USERNAME', "Enter the SSH username for the jumpbox: ")
          jumpbox_key_path = env_manager.get_or_prompt_env_var('JUMPBOX_KEY', "Enter the path to your jumpbox SSH key: ")

     # Target Host
     target_username = env_manager.get_or_prompt_env_var('TARGET_USERNAME', "Enter the SSH username for the targets: ")
     target_key_path = env_manager.get_or_prompt_env_var('TARGET_KEY', "Enter the path to your target SSH key: ")
     
     return jumpbox, jumpbox_username, jumpbox_key_path,  target_username, target_key_path

def main_menu():
     print("\nSelect an option:")
     print("1. Add a host")
     print("2. Load hosts from file")
     print("3. Save hosts to file")
     print("4. Run command on hosts")
     print("5. Configure")
     print("6. Exit")
     
     choice = input("Enter your choice: ")

     return choice

def display_commands_menu():
     command_generator = CommandGenerator()
     commands = list(command_generator.commands.keys())

     while True:
        print("Select a command to run:")
        for idx, command in enumerate(commands, 1):
            print(f"{idx}. {command}")
        print(f"{len(commands) + 1}. Back")

        choice = input("Enter your choice: ")

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(commands):
                command_name = commands[choice - 1]
                return command_name
            elif choice == len(commands) + 1:
                return None
        print("\n\033[1;31mInvalid command choice, please try again.\033[0m")

def modify_commands_menu():
     command_generator = CommandGenerator()
     while True:
          command_name = input("Enter the command name (no spaces) or exit: ")
          if command_name.lower() == 'exit':
               break

          commands = {}
          while True:
               distro = input("\033[32mArtifactor will look in the /etc/os-release ID= field for the os. \n"
                              "Common entries for this are ubuntu, debian, fedora, centos, rhel, and arch. \n"
                              "Enter the distribution name (or type 'done' to finish): \033[0m").lower()
               if distro == 'done':
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
               confirm = input(f"You entered '{distro}' with the command '{command}'. Is that correct? (y/n): ").lower()
               if confirm.lower() in ['yes', 'y']:
                    if command == 'null':
                         command = None
                    commands[distro] = command

          if commands:
               command_generator.modify_commands(command_name, commands)
               print(f"Command '{command_name}' added/updated successfully.")
               break
          else:
               print("Invalid option. No command added.")

def configure_menu():
     env_manager = EnvManager()
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
               modify_commands_menu()
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