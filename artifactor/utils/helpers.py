def common_help(instance, arg, run_case=False):
    '''List available menu commands and usage: help [<arg>]'''
    if arg:
        command_method = getattr(instance, f'do_{arg}', None)
        if command_method and command_method.__doc__:
            help_info = command_method.__doc__.split(':', 1)
            description = help_info[0].strip()
            usage = help_info[1].strip() if len(help_info) > 1 else ""
            print(f"\033[1;31m{arg}\033[0m\n\033[1;31mdescription:\033[0m {description}\n")
            print(f"\033[1;31musage:\033[0m {usage}\n")
        else:
            print(f"No help available for {arg}\n")
    else:
        print("\033[1;31musage:\033[0m <command> [<args>]")

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