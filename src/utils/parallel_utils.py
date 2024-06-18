import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_and_create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_log_name(host):
    # Replace periods with dashes for IP addresses
    safe_host = host.replace('.', '-')
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f'logs/{safe_host}_{timestamp}.txt'

def write_output(file_path, text):
    with open(file_path, 'a') as f:
        f.write(text + '\n')

def execute_commands_in_parallel(command_func, hosts, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
    if not hosts:
        print("No hosts available to run the command.")
        return {}
    
    check_and_create_directory('logs')

    results = {}
    with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
        future_to_host = {
            executor.submit(command_func, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path): host for host in hosts
        }
        for future in as_completed(future_to_host):
            host = future_to_host[future]

            log_name = generate_log_name(host)
            try:
                host, result = future.result()
                results[host] = result
                write_output(log_name, f"Results for {host}:\n{result}")
                print(f"\n\033[1;32mHost {host} results written to {log_name}\033[0m")
            except Exception as e:
                results[host] = str(e)
    return results
