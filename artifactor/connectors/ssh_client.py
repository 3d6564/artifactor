import paramiko
import socket
import winrm
from sshtunnel import SSHTunnelForwarder
from contextlib import closing

       
class SSHClient:

    def create_ssh_forwarder(self, ssh_host, ssh_port, ssh_username, ssh_password=None, ssh_key_path=None, remote_bind_address=[]):
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            ssh_pkey=ssh_key_path,
            remote_bind_addresses=remote_bind_address,
            local_bind_address=('localhost', 0)  # OS picks port when 0
        )
        tunnel.start()
        # The below should be logged but doesn't need output to user
        #print(f"Local bind ports: {tunnel.local_bind_ports}")
        return tunnel
    
    def is_port_open(self, host, port):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1)
            return sock.connect_ex((host, port)) == 0

    def create_winrm_session(self, host, port, username, password):
        local_port = port  # Assuming the first local bind port is for WinRM
        winrm_session = winrm.Session(
            f'http://{host}:{local_port}/wsman',
            auth=(username, password),
            transport='ntlm'
        )
        return winrm_session
    
    def execute_ssh_command(self, command, ssh_host, ssh_port, ssh_username, ssh_key_path=None, password=None):
        """
        Execute a command on a remote host via SSH.

        Args:
            command (str): The command to execute on the remote host.
            ssh_host (str): The hostname or IP address of the remote host.
            ssh_port (int): The port to use for the SSH connection.
            ssh_username (str): The username to use for the SSH connection.
            ssh_key_path (str, optional): The path to the SSH key file. Defaults to None.
            password (str, optional): The password to use for the SSH connection. Defaults to None.

        Returns:
            tuple: A tuple containing the command output and error (output, error).
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if ssh_key_path:
            ssh_client.connect(
                hostname=ssh_host,
                port=ssh_port,
                username=ssh_username,
                key_filename=ssh_key_path
            )
        else:
            ssh_client.connect(
                hostname=ssh_host,
                port=ssh_port,
                username=ssh_username,
                password=password
            )

        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode() if stdout else None
        error = stderr.read().decode() if stderr else None

        ssh_client.close()
        return output, error

    def run_command_on_host(self, env_manager, command, os_type, host, 
                            jumpbox=None, jumpbox_username=None, target_username=None, 
                            jumpbox_password=None, jumpbox_key_path=None, 
                            target_password=None, target_key_path=None):
        output = None
        use_jumpbox = env_manager.env_vars['USE_JUMPBOX'].lower() in ['y']
        
        use_target_password = env_manager.env_vars['USE_TARGET_PASSWORD'].lower() in ['y']
        use_jumpbox_password = env_manager.env_vars['USE_JUMPBOX_PASSWORD'].lower() in ['y']
        target_username = env_manager.env_vars['TARGET_USERNAME']
        win_username = env_manager.env_vars['WIN_USERNAME']
        win_password = env_manager.env_vars['WIN_PASSWORD']

        if use_target_password:
            target_password = env_manager.env_vars['TARGET_PASSWORD']
            target_key_path = None
        else:
            target_key_path = env_manager.env_vars['TARGET_KEY']
            target_password = None

        try:
            if use_jumpbox:
                jumpbox = env_manager.env_vars['JUMPBOX']
                jumpbox_username = env_manager.env_vars['JUMPBOX_USERNAME']
                if use_jumpbox_password:
                    jumpbox_password = env_manager.env_vars['JUMPBOX_PASSWORD']
                else:
                    jumpbox_key_path = env_manager.env_vars['JUMPBOX_KEY']
                print(f"Using jumpbox to connect to {host}...")
                # This is designed for JUMPBOX to be ONLY linux for now
                tunnel = self.create_ssh_forwarder(ssh_host=jumpbox,
                                                   ssh_port=22,
                                                   ssh_username=jumpbox_username,
                                                   ssh_password=jumpbox_password,
                                                   ssh_key_path=jumpbox_key_path,
                                                   remote_bind_address=((host, 5985 if os_type in ('windows', 'win-winrm') else 22),))
                if os_type in ('windows', 'win-winrm'):
                    print(f'Creating WinRM session for {host}...')
                    winrm_session = self.create_winrm_session('localhost',
                                                              tunnel.local_bind_ports[0],
                                                              win_username,
                                                              win_password)
                    print('WinRM session established...')
                    result = winrm_session.run_cmd(command)
                    output = result.std_out.decode('utf-8') if result.std_out else None
                    error = result.std_err.decode('utf-8') if result.std_err else None
                else:
                    print(f'Creating SSH session for {host}...')
                    output, error = self.execute_ssh_command(command,
                                                             'localhost',
                                                             tunnel.local_bind_ports[0],
                                                             target_username,
                                                             target_key_path,
                                                             target_password)
                tunnel.stop()
            else:
                print(f"Using SSH to connect to {host}...")
                if os_type in ('windows', 'win-winrm'):
                    print('Creating WinRM session...')
                    winrm_session = self.create_winrm_session(host,
                                                              5985,
                                                              win_username,
                                                              win_password)
                    print('WinRM session established...')
                    result = winrm_session.run_cmd(command)
                    output = result.std_out.decode('utf-8') if result.std_out else None
                    error = result.std_err.decode('utf-8') if result.std_err else None
                else:
                    print('Creating SSH session...')
                    output, error = self.execute_ssh_command(command,
                                                             host,
                                                             22,
                                                             target_username,
                                                             target_key_path,
                                                             target_password)
                if error:
                    print(f'Error: {error}')
                    output = error
            return host, output
        except Exception as e:
            print(f"Error: {e}")
            return host, str(e)
