import os
import paramiko


def create_ssh_client(hostname, username, key_path, proxy_command=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if proxy_command:
        client.connect(hostname, username=username, key_filename=key_path, sock=proxy_command)
    else:
        client.connect(hostname, username=username, key_filename=key_path)
    return client

def run_command_on_host(command, host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
    use_jumpbox = os.getenv('USE_JUMPBOX', 'False').lower() in ['true', '1', 't']
    try:
        if use_jumpbox == True:
            jumpbox_client = create_ssh_client(jumpbox, jumpbox_username, jumpbox_key_path)
            jumpbox_transport = jumpbox_client.get_transport()
            dest_addr = (host, 22)
            local_addr = (jumpbox, 22)
            channel = jumpbox_transport.open_channel("direct-tcpip", dest_addr, local_addr)
            target_client = create_ssh_client(host, target_username, target_key_path, proxy_command=channel)
        else:
            target_client = create_ssh_client(host, target_username, target_key_path)

        stdin, stdout, stderr = target_client.exec_command(command)
        output = stdout.read() + stderr.read()

        if use_jumpbox == True:
            target_client.close()
            jumpbox_client.close()
        else:
            target_client.close()

        return host, output.decode()
    except Exception as e:
        return host, str(e)
