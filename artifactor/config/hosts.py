import os
import shutil

class HostManager:
    def __init__(self, hosts_file='host_file'):
        self.host_template = 'host_file.template'
        self.hosts_file = hosts_file
        self.hosts = self.load_hosts()

    def add_host(self, host):
        if host not in self.hosts:
            self.hosts.append(host)
            self.save_hosts()
            return True
        return False

    def load_hosts(self):
        try:
            with open(self.hosts_file, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            print(f"\033[1;33mHosts file {self.hosts_file} does not exist... cloning template")
            try:
                shutil.copyfile(self.host_template, self.hosts_file)
                with open(self.hosts_file, 'r') as f:
                    return [line.strip() for line in f.readlines() if line.strip()]
            except:
                print('\033[1;31mWarning: You do not have a hosts file.')
            return []

    def save_hosts(self):
        with open(self.hosts_file, 'w') as file:
            for host in self.hosts:
                file.write(f"{host}\n")
