import os
import paramiko
from config import EnvManager

class SSHClient:

    def create_ssh_client(self, hostname, username, password=None, key_path=None, proxy_command=None):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_args = {'hostname': hostname, 'username': username}
    
        if proxy_command:
            if password:
                client.connect(**connect_args, password=password, sock=proxy_command)
            elif key_path:
                client.connect(**connect_args, key_filename=key_path, sock=proxy_command)
            else:
                raise ValueError("Either password or key_path must be provided for authentication with proxy_command")
        else:
            if password:
                client.connect(**connect_args, password=password)
            elif key_path:
                client.connect(**connect_args, key_filename=key_path)
            else:
                raise ValueError("Either password or key_path must be provided for authentication")
        
        return client

    def create_proxy_channel(self, jumpbox_client, host, jumpbox):
        jumpbox_transport = jumpbox_client.get_transport()
        dest_addr = (host, 22)
        local_addr = (jumpbox, 22)
        return jumpbox_transport.open_channel("direct-tcpip", dest_addr, local_addr)

    def execute_command(self, client, command):
        stdin, stdout, stderr = client.exec_command(command)
        return (stdout.read() + stderr.read()).decode()

    def run_command_on_host(self, command, host, jumpbox, jumpbox_username, target_username, jumpbox_password=None, jumpbox_key_path=None, target_password=None, target_key_path=None):
        env_manager = EnvManager()
        use_jumpbox = env_manager.get_env_var('USE_JUMPBOX').lower() in ['y']
        try:
            if use_jumpbox:
                jumpbox_client = self.create_ssh_client(jumpbox, 
                                                        jumpbox_username, 
                                                        password=jumpbox_password, 
                                                        key_path=jumpbox_key_path)
                channel = self.create_proxy_channel(jumpbox_client, host, jumpbox)
                target_client = self.create_ssh_client(host, 
                                                       target_username, 
                                                       password=target_password, 
                                                       key_path=target_key_path, 
                                                       proxy_command=channel)
            else:
                target_client = self.create_ssh_client(host, 
                                                       target_username, 
                                                       password=target_password, 
                                                       key_path=target_key_path)

            output = self.execute_command(target_client, command)
            target_client.close()
            if use_jumpbox:
                jumpbox_client.close()

            return host, output
        except Exception as e:
            return host, str(e)
