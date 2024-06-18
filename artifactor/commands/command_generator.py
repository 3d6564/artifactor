from connectors import SSHClient


class CommandGenerator:
    def __init__(self):
        self.ssh_client = SSHClient()

    def get_processes(self, host, jumpbox, jumpbox_key_path, target_key_path, jumpbox_username, target_username):
        return self.ssh_client.run_command_on_host('ps aux', host, jumpbox, jumpbox_key_path, target_key_path, jumpbox_username, target_username)

    def get_users(self, host, jumpbox, jumpbox_key_path, target_key_path, jumpbox_username, target_username):
        return self.ssh_client.run_command_on_host('cat /etc/passwd', host, jumpbox, jumpbox_key_path, target_key_path, jumpbox_username, target_username)

    def get_system_info(self, host, jumpbox, jumpbox_key_path, target_key_path, jumpbox_username, target_username):
        return self.ssh_client.run_command_on_host('uname -a', host, jumpbox, jumpbox_key_path, target_key_path, jumpbox_username, target_username)
