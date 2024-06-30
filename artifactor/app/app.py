import os
from .menu import print_ascii_art, main_menu, display_commands_menu, configure_menu
from config import EnvManager, HostManager
from commands import CommandGenerator


def main():
    print_ascii_art()

    print("\nInitializing environment...\n")

    # initialize environment
    env_manager = EnvManager()
    env_manager.initialize_env()

    # initialize hosts
    host_manager = HostManager()
    if host_manager.hosts:
        print("\033[1;32mHosts have been initialized.\033[0m")

    # initialize commands
    cmd_generator = CommandGenerator()
    if cmd_generator.commands:
        print("\033[1;32mCommands have been initialized.\033[0m")

    
    while True:
        choice = main_menu()

        if choice == '1':
            new_host = input("Enter the hostname or IP address: ")
            if host_manager.add_host(new_host):
                print(f"\033[1;32mHost {new_host} added. Hosts saved to {host_manager.hosts_file}.\033[0m")
            else:
                print(f"Host {new_host} is already in the list.")
        elif choice == '2':
            host_manager.hosts_file = input("Enter the file path and name (path/to/file): ")
            host_manager.hosts = host_manager.load_hosts()
            print(f"\033[1;32mHosts loaded from {host_manager.hosts_file}: {host_manager.hosts}\033[0m")
        elif choice == '3':
            if not host_manager.hosts:
                print("\033[1;31mNo hosts available. Please add hosts first.\033[0m")
                continue

            command_name = display_commands_menu()
            if command_name:
                cmd_generator.run_command(command_name, 
                                        host_manager.hosts,
                                        env_manager.env_vars.get('JUMPBOX'),
                                        env_manager.env_vars.get('JUMPBOX_USERNAME'), 
                                        env_manager.env_vars.get('TARGET_USERNAME'), 
                                        env_manager.env_vars.get('JUMPBOX_KEY'), 
                                        env_manager.env_vars.get('TARGET_KEY'))

        elif choice == '4':
            configure_menu(env_manager)
        elif choice == '5':
            for host in host_manager.hosts:
                print(f"{host}: {cmd_generator.ping_ttl(host)}")
        elif choice == '6':
            break
        else:
            print("\n\033[1;31mInvalid choice, please try again.\033[0m")

if __name__ == "__main__":
    main()