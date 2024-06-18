import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from artifactor.utils.logger import Logger

class ParallelExecutor:
    def __init__(self):
        self.logger = Logger()
    

    def execute_commands_in_parallel(self, command_func, hosts, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
        if not hosts:
            print("No hosts available to run the command.")
            return {}

        results = {}
        with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
            future_to_host = {
                executor.submit(command_func, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path): host for host in hosts
            }
            for future in as_completed(future_to_host):
                host = future_to_host[future]
                log_name = self.logger.generate_log_name(host)
                try:
                    host, result = future.result()
                    results[host] = result
                    self.logger.write_output(log_name, f"Results for {host}:\n{result}")
                    print(f"\n\033[1;32mHost {host} results written to {log_name}\033[0m")
                except Exception as e:
                    results[host] = str(e)
                    self.logger.write_output(log_name, f"Error for {host}:\n{e}")
                    print(f"Host {host} error written to {log_name}")
        return results
