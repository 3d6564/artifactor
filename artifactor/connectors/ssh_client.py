import os
import paramiko
import socket
import winrm
from contextlib import closing
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
    
    def is_port_open(self, host, port):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1)
            return sock.connect_ex((host, port)) == 0

    def create_proxy_channel(self, jumpbox_client, host, jumpbox):
        jumpbox_transport = jumpbox_client.get_transport()
        dest_addr = (host, 22)
        local_addr = (jumpbox, 22)
        return jumpbox_transport.open_channel("direct-tcpip", dest_addr, local_addr)

    def create_winrm_proxy_channel(self, jumpbox_client, host, local_addr):
        jumpbox_transport = jumpbox_client.get_transport()
        dest_addr = (host, 5985)
        local_addr = (local_addr, 5985)
        return jumpbox_transport.open_channel("direct-tcpip", dest_addr, local_addr)
    """
    def create_port_forward(self, jumpbox_client, host, win_username, win_password):
        jumpbox_transport = jumpbox_client.get_transport()
        local_addr = '127.0.0.1'
        local_port = 5985
        host_port = 5985

        jumpbox_transport.request_port_forward(local_addr, local_port, host, host_port)
        if self.is_port_open(local_addr, local_port):
                        print(f"Port forwarding established from local {local_addr} to remote {host}")
        # Create WinRM session using forwarded port
        
        return winrm_session
    """
    def execute_command(self, client, command):
        stdin, stdout, stderr = client.exec_command(command)
        return (stdout.read() + stderr.read()).decode()

    def run_command_on_host(self, command, os_type, host, jumpbox, jumpbox_username, target_username, jumpbox_password=None, jumpbox_key_path=None, target_password=None, target_key_path=None):
        env_manager = EnvManager()
        use_jumpbox = env_manager.get_env_var('USE_JUMPBOX').lower() in ['y']
        use_port_forward = env_manager.get_env_var('USE_PORT_FORWARD').lower() in ['y']
        win_username = env_manager.get_env_var('WIN_USERNAME')
        win_password = env_manager.get_env_var('WIN_PASSWORD')

        output = None

        try:
            if use_jumpbox:
                jumpbox_client = self.create_ssh_client(jumpbox, 
                                                        jumpbox_username, 
                                                        password=jumpbox_password, 
                                                        key_path=jumpbox_key_path)
                if os_type == 'windows' or os_type == 'win-winrm':
                    if use_port_forward:
                        #local_addr = '127.0.0.1'
                        #print('Creating winrm proxy')
                        #winrm_session = self.create_winrm_proxy_channel(jumpbox_client, host, jumpbox)
                        #print('Proxy created...')
                        winrm_session = winrm.Session(f'{host}', auth=(win_username, win_password), transport='ntlm')
                        print('WinRM session created...')
                        # Check if the port forwarding was successful
                        output = winrm_session.run_cmd(command).std_out.decode()
                        # Clean empty lines
                        output = '\n'.join(line for line in output.splitlines() if line.strip())
                        #print('Result received...')
                else:
                    channel = self.create_proxy_channel(jumpbox_client, host, jumpbox)
                    target_client = self.create_ssh_client(host, 
                                                           target_username, 
                                                           password=target_password, 
                                                           key_path=target_key_path, 
                                                           proxy_command=channel)
                    print('SSH session created...')
                    output = self.execute_command(target_client, command)
            else:
                if os_type == 'windows' or os_type == 'win-winrm':
                    if use_port_forward:
                        #local_addr = '127.0.0.1'
                        #print('Creating winrm proxy')
                        #winrm_session = self.create_winrm_proxy_channel(jumpbox_client, host, jumpbox)
                        #print('Proxy created...')
                        winrm_session = winrm.Session(f'{host}', auth=(win_username, win_password), transport='ntlm')
                        print('WinRM session created...')
                        # Check if the port forwarding was successful
                        #print(command)
                        output = winrm_session.run_cmd(command).std_out.decode()
                        print('Result received...')
                else:
                    target_client = self.create_ssh_client(host, 
                                                        target_username, 
                                                        password=target_password, 
                                                        key_path=target_key_path)
                    output = self.execute_command(target_client, command)
            try:
                target_client.close()
            except:
                print('No target client to close... Maybe winrm was used..')
            if use_jumpbox:
                try:
                    jumpbox_client.close()
                except:
                    print('Maybe no jumpbox was configured...')

            return host, output
        except Exception as e:
            return host, str(e)
