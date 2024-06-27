import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import Logger

class ParallelExecutor:
    def __init__(self):
        self.logger = Logger()
    

    def execute_commands_in_parallel(self, command_func, host_list, jumpbox, jumpbox_username, target_username, jumpbox_password=None, jumpbox_key_path=None, target_password=None, target_key_path=None):
        if not host_list:
            print("No hosts available to run the command.")
            return {}

        results = {}
        with ThreadPoolExecutor(max_workers=len(host_list)) as executor:
            #print(f"Running {command} on hosts {hosts}...")
            future_to_host = {
                executor.submit(command_func, 
                                values["command"], 
                                values["os_type"],
                                host, 
                                jumpbox, 
                                jumpbox_username=jumpbox_username, 
                                target_username=target_username, 
                                jumpbox_password=jumpbox_password, 
                                jumpbox_key_path=jumpbox_key_path, 
                                target_password=target_password, 
                                target_key_path=target_key_path): host for host, values in host_list.items()
            }
            for future in as_completed(future_to_host):
                host = future_to_host[future]
                log_name = self.logger.generate_log_name(host, 'test')
                try:
                    host, result = future.result()
                    results[host] = result
                    self.logger.write_output(log_name, result)
                    print(f"\033[1;32mHost {host} results written to {log_name}\033[0m")
                except Exception as e:
                    results[host] = str(e)
                    self.logger.write_output(log_name, f"Error for {host}:\n{e}")
                    print(f"Host {host} error written to {log_name}")
        return results
    
    def shutdown_executor(self):
        self.executor.shutdown(wait=True)
