from .ssh_utils import run_command_on_host


def list_processes(host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
    return run_command_on_host('ps aux', host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)

def list_users(host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
    return run_command_on_host('cat /etc/passwd', host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)

def get_system_info(host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path):
    return run_command_on_host('uname -a', host, jumpbox, jumpbox_username, jumpbox_key_path, target_username, target_key_path)
