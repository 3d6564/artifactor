import os
from .menu import print_ascii_art, print_menu
from config import EnvManager
from utils import HostManager
from commands import CommandGenerator, ParallelExecutor


def main():
    env_manager = EnvManager()
    host_manager = HostManager()
    cmd_generator = CommandGenerator()
    cmd_executor = ParallelExecutor()

    
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
    commands = {
        '1': cmd_generator.get_processes,
        '2': cmd_generator.get_users,
        '3': cmd_generator.get_system_info,
    }

    while True:
        print_menu()

        choice = input("Enter your choice: ")

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
            print(f"\n\033[1;32mHosts loaded from {file_path}: {hosts}\033[0m")
        elif choice == '3':
            host_manager.save_hosts(file_path, hosts)
            print(f"\n\033[1;32mHosts saved to {file_path}.\033[0m")
        elif choice == '4':
            if not hosts:
                print("\n\033[1;31mNo hosts available. Please add hosts first.\033[0m")
                continue

            print("\nSelect a command to run:")
            print("1. List Processes")
            print("2. List Users")
            print("3. Get System Info")

            cmd_choice = input("Enter your choice: ")
            if cmd_choice in commands:
                cmd_executor.execute_commands_in_parallel(commands[cmd_choice], hosts, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)
            else:
                print("\n\033[1;31mInvalid command choice, please try again.\033[0m")
        elif choice == '5':
            env_manager.set_jumpbox_use()
        elif choice == '6':
            break
        else:
            print("\n\033[1;31mInvalid choice, please try again.\033[0m")

if __name__ == "__main__":
    main()