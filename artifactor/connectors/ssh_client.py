import os
import paramiko
from config import EnvManager

class SSHClient:

    def create_ssh_client(self, hostname, username, key_path, proxy_command=None):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if proxy_command:
            client.connect(hostname, username=username, key_filename=key_path, sock=proxy_command)
        else:
            client.connect(hostname, username=username, key_filename=key_path)
        return client

    def run_command_on_host(self, command, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
        env_manager = EnvManager()
        use_jumpbox = env_manager.get_env_var('USE_JUMPBOX').lower() in ['y']
        try:
            if use_jumpbox:
                jumpbox_client = self.create_ssh_client(jumpbox, jumpbox_username, jumpbox_key_path)
                jumpbox_transport = jumpbox_client.get_transport()
                dest_addr = (host, 22)
                local_addr = (jumpbox, 22)
                channel = jumpbox_transport.open_channel("direct-tcpip", dest_addr, local_addr)
                target_client = self.create_ssh_client(host, target_username, target_key_path, proxy_command=channel)
            else:
                target_client = self.create_ssh_client(host, target_username, target_key_path)

            stdin, stdout, stderr = target_client.exec_command(command)
            output = stdout.read() + stderr.read()

            target_client.close()
            if use_jumpbox:
                jumpbox_client.close()

            return host, output.decode()
        except Exception as e:
            return host, str(e)
        
    def detect_os(self, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
        os_command = 'uname'  # Basic command to identify the OS type
        host, output = self.run_command_on_host(os_command, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)
        if 'Linux' in output:
            # check between different linux distributions
            os_command = 'cat /etc/os-release'
            host, output = self.run_command_on_host(os_command, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)

            if 'Debian' in output or 'Ubuntu' in output:
                return 'debian'
            elif 'CentOS' in output or 'Red Hat' in output or 'Fedora' in output:
                return 'centos'
        else:
            os_command = 'ver'  # Command to identify Windows OS
            host, output = self.run_command_on_host(os_command, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)
            if 'Windows' in output:
                return 'windows'
        return 'unknown'