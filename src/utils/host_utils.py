import os

def load_hosts(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    return []

def save_hosts(file_path, hosts):
    with open(file_path, 'w') as file:
        for host in hosts:
            file.write(f"{host}\n")
