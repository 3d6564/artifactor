import os

class HostManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.hosts = self.load_hosts()

    def add_host(self, host):
        if host not in self.hosts:
            self.hosts.append(host)
            self.save_hosts()
            return True
        return False

    def load_hosts(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                return [line.strip() for line in file.readlines()]
        return []

    def save_hosts(self):
        with open(self.file_path, 'w') as file:
            for host in self.hosts:
                file.write(f"{host}\n")
