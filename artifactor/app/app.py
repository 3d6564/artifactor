import os
from .menu import print_ascii_art, main_menu, display_commands_menu, configure_menu
from config import EnvManager
from utils import HostManager
from commands import CommandGenerator, ParallelExecutor


def main():
    env_manager = EnvManager()
    host_manager = HostManager()
    cmd_generator = CommandGenerator()
    
    print_ascii_art()
    file_path = 'host_list'

    # ------------------------ #
    jumpbox_key_path = env_manager.get_or_prompt_env_var('JUMPBOX_KEY', "Enter the path to your jumpbox SSH key: ")
    jumpbox_username = env_manager.get_or_prompt_env_var('JUMPBOX_USERNAME', "Enter the SSH username for the jumpbox: ")

    target_key_path = env_manager.get_or_prompt_env_var('TARGET_KEY', "Enter the path to your target host SSH key: ")
    target_username = env_manager.get_or_prompt_env_var('TARGET_USERNAME', "Enter the SSH username for the target hosts: ")
    use_jumpbox = env_manager.get_or_prompt_env_var('USE_JUMPBOX', "Enter True or False to use a jumpbox: ")
    if use_jumpbox not in ["True", "False"]:
        use_jumpbox = input("Invalid input. Do you want to use a jumpbox? (True/False): ").strip()
        env_manager.set_env_var('USE_JUMPBOX', use_jumpbox)
    if use_jumpbox:
        jumpbox = env_manager.get_or_prompt_env_var('JUMPBOX', "Enter the hostname or ip of a jumpbox: ")
    

    # ------------------------ #
    hosts = host_manager.load_hosts(file_path)
    print(f"Hosts loaded from {file_path} file...")

    while True:
        choice = main_menu()
        print('\n')

        if choice == '1':
            new_host = input("Enter the hostname or IP address: ")
            if new_host not in hosts:
                hosts.append(new_host)
                print(f"Host {new_host} added.")
            else:
                print(f"Host {new_host} is already in the list.")
        elif choice == '2':
            new_file = input("Enter the file path and name (path/to/file): ")
            hosts = host_manager.load_hosts(new_file)
            print(f"\033[1;32mHosts loaded from {file_path}: {hosts}\033[0m")
        elif choice == '3':
            host_manager.save_hosts(file_path, hosts)
            print(f"\033[1;32mHosts saved to {file_path}.\033[0m")
        elif choice == '4':
            if not hosts:
                print("\033[1;31mNo hosts available. Please add hosts first.\033[0m")
                continue

            command_name = display_commands_menu()
            cmd_generator.run_command(command_name, 
                                      hosts, 
                                      jumpbox, 
                                      jumpbox_username, 
                                      jumpbox_key_path, 
                                      target_username, 
                                      target_key_path)

        elif choice == '5':
            configure_menu()
        elif choice == '6':
            break
        else:
            print("\n\033[1;31mInvalid choice, please try again.\033[0m")

if __name__ == "__main__":
    main()