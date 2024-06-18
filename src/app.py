import os
from dotenv import load_dotenv, set_key
from .utils import load_hosts, save_hosts, list_processes, list_users, get_system_info, execute_commands_in_parallel


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

def check_and_create_env_file():
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            pass

def get_or_set_env_var(var_name, prompt_text):
    value = os.getenv(var_name)
    if value is None:
        value = input(prompt_text)
        set_key('.env', var_name, value)
    return value

def main():
    load_dotenv()
    check_and_create_env_file()
    
    print_ascii_art()
    file_path = 'host_list'

    # ------------------------ #
    jumpbox_key_path = get_or_set_env_var('JUMPBOX_KEY', "Enter the path to your jumpbox SSH key: ")
    jumpbox_username = get_or_set_env_var('JUMPBOX_USERNAME', "Enter the SSH username for the jumpbox: ")

    target_key_path = get_or_set_env_var('TARGET_KEY', "Enter the path to your target host SSH key: ")
    target_username = get_or_set_env_var('TARGET_USERNAME', "Enter the SSH username for the target hosts: ")
    jumpbox = get_or_set_env_var('JUMPBOX', "Enter the hostname or IP address of the jumpbox: ")

    # ------------------------ #
    hosts = load_hosts(file_path)
    print(f"Hosts loaded from {file_path} file...")
    commands = {
        '1': list_processes,
        '2': list_users,
        '3': get_system_info,
    }

    while True:
        print("\nSelect an option:")
        print("1. Add a host")
        print("2. Load hosts from file")
        print("3. Save hosts to file")
        print("4. Run command on hosts")
        print("5. Exit")

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
            hosts = load_hosts(new_file)
            print(f"\n\033[1;32mHosts loaded from {file_path}: {hosts}\033[0m")
        elif choice == '3':
            save_hosts(file_path, hosts)
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
                execute_commands_in_parallel(commands[cmd_choice], hosts, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)
            else:
                print("\n\033[1;31mInvalid command choice, please try again.\033[0m")
        elif choice == '5':
            break
        else:
            print("\n\033[1;31mInvalid choice, please try again.\033[0m")
