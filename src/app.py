import os
from dotenv import load_dotenv, set_key, dotenv_values
from .utils import load_hosts, save_hosts, get_processes, get_users, get_system_info, execute_commands_in_parallel


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

def get_env_var(var_name):
    return os.getenv(var_name)

def set_env_var(var_name, var_value):
    env_vars = dotenv_values(".env")
    env_vars[var_name] = var_value
    with open(".env", "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

def get_or_prompt_env_var(var_name, prompt_text):
    value = get_env_var(var_name)
    if value is None:
        value = input(prompt_text)
        set_env_var(var_name, value)
    return value

def set_jumpbox_use():
    jumpbox_use = input("Do you want to use a jumpbox? (True/False): ").strip()
    while jumpbox_use not in ["True", "False"]:
        jumpbox_use = input("Invalid input. Do you want to use a jumpbox? (True/False): ").strip()
    set_env_var('USE_JUMPBOX', jumpbox_use)
    load_dotenv(override=True)
    print(f"\n\033[1;32mJumpbox usage set to: {jumpbox_use}\033[0m")

def main():
    load_dotenv()
    check_and_create_env_file()
    
    print_ascii_art()
    file_path = 'host_list'

    # ------------------------ #
    jumpbox_key_path = get_or_prompt_env_var('JUMPBOX_KEY', "Enter the path to your jumpbox SSH key: ")
    jumpbox_username = get_or_prompt_env_var('JUMPBOX_USERNAME', "Enter the SSH username for the jumpbox: ")

    target_key_path = get_or_prompt_env_var('TARGET_KEY', "Enter the path to your target host SSH key: ")
    target_username = get_or_prompt_env_var('TARGET_USERNAME', "Enter the SSH username for the target hosts: ")
    use_jumpbox = get_or_prompt_env_var('USE_JUMPBOX', "Enter True or False to use a jumpbox: ")
    if use_jumpbox not in ["True", "False"]:
        use_jumpbox = input("Invalid input. Do you want to use a jumpbox? (True/False): ").strip()
        set_key('.env', 'USE_JUMPBOX', use_jumpbox)
    if use_jumpbox:
        jumpbox = get_or_prompt_env_var('JUMPBOX', "Enter the hostname or ip of a jumpbox: ")
    

    # ------------------------ #
    hosts = load_hosts(file_path)
    print(f"Hosts loaded from {file_path} file...")
    commands = {
        '1': get_processes,
        '2': get_users,
        '3': get_system_info,
    }

    while True:
        print("\nSelect an option:")
        print("1. Add a host")
        print("2. Load hosts from file")
        print("3. Save hosts to file")
        print("4. Run command on hosts")
        print("5. Set jumpbox usage")
        print("6. Exit")

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
            set_jumpbox_use()
        elif choice == '6':
            break
        else:
            print("\n\033[1;31mInvalid choice, please try again.\033[0m")
