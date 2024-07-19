import os


def common_help(instance, arg, run_case=False):
    """
    This function helps build the help/? section in the application to maintain a 
    consistent help output.

    Args:
        instance: The instance of the class with command methods.
        arg (str): The specific command to display help for.
        run_case (bool): Include/exclude commands that start with 'get_' in a 
            separate 'run_commands' section.
    """
    if arg:
        command_method = getattr(instance, f'do_{arg}', None)
        if command_method and command_method.__doc__:
            help_info = command_method.__doc__.split(':', 1)
            description = help_info[0].strip()
            usage = help_info[1].strip() if len(help_info) > 1 else ""
            print(f"\033[1;31musage:\033[0m {usage}\n")
            print(f"{description}\n")
        else:
            print(f"No help available for {arg}\n")
    else:
        print("\033[1;31musage:\033[0m <command> [<args>]")
        class_doc = instance.__doc__
        if class_doc:
            print(f"\n{class_doc}")

        run_commands = []
        commands = []

        for attr in dir(instance):
            if attr.startswith('do_'):
                command_name = attr[3:]
                command_method = getattr(instance, attr)
                if command_method and command_method.__doc__:
                    help_info = command_method.__doc__.split(':', 1)
                    description = help_info[0].strip()
                    if run_case and command_name.startswith('get_'):
                        run_commands.append((command_name, description))
                    else:
                        commands.append((command_name, description))

        if commands:
            print("\n\033[1;31mcommands:\033[0m")
            for command_name, description in commands:
                print(f"    {command_name.ljust(25)} {description.lower()}")

        if run_case and run_commands:
            print("\n\033[1;31mrun_commands:\033[0m")
            for command_name, description in run_commands:
                # Retrieve description from cmd_manager if instance is RunCmd
                description = instance.cmd_manager.commands[command_name].get('description', 'No description available')
                print(f"    {command_name.ljust(25)} {description.lower()}")
        print()

def check_and_create_directory(directory):
    """
    Check if a directory exists, and create it if it does not.

    Args:
        directory (str): The path of the directory to check/create.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def check_and_create_file(file):
    """
    Check if a file exists, and create it if it does not.

    Args:
        file (str): The path of the file to check/create.
    """
    if not os.path.exists(file):
        open(file, 'a').close()


def clean_results(result):
    """
    Cleans the results of output of white space.

    Args:
        result (str): Results from a command executed on a remote host.
    """
    lines = result.splitlines()
    cleaned_lines = [line for line in lines if line.strip()]
    return "\n".join(cleaned_lines)