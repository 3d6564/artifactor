from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import Logger, clean_results

class ParallelExecutor:
    def __init__(self):
        self.logger = Logger()

    def execute_commands_in_parallel(self, command_func, env_manager, host_list):
        if not host_list:
            print("No hosts available to run the command.")
            return {}

        results = {}

        with ThreadPoolExecutor(max_workers=len(host_list)) as executor:
            future_to_host = {
                executor.submit(command_func,
                                env_manager,
                                values["command"],
                                values["os_type"],
                                host,
                                values["sudo"]): (host, values["command_name"]) for host, values in host_list.items()
            }
            for future in as_completed(future_to_host):
                host, command_name = future_to_host[future]
                log_name = self.logger.generate_host_cmd_log(host, command_name)
                try:
                    host, result = future.result()
                    results[host] = clean_results(result)
                    self.logger.write_output(log_name, result)

                    if result.startswith('error'):
                        print(f"\033[1;31mHost {host} {result}\033[0m")
                        print(f"\033[1;31mHost {host} error written to {log_name}\033[0m")
                    else:
                        print(f"\033[1;32mHost {host} results written to {log_name}\033[0m")
                except Exception as e:
                    results[host] = str(e)
                    self.logger.write_output(log_name, f"Error for {host}:\n{e}")
                    print(f"\033[1;DmHost {host} error written to {log_name}\033[0m")
        return results
    
    def shutdown_executor(self):
        self.executor.shutdown(wait=True)
