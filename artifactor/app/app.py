import pyfiglet
import random
from termcolor import colored
from .menu import MainCmd
from config import EnvManager, HostManager, CommandManager, CommandExecutor
from utils import Logger, class_logger


logger_instance = Logger()

@class_logger(logger_instance)
class Artifactor():

    def __init__(self):
        self.initialize_environment()

    def initialize_environment(self):
        print("\nInitializing environment...\n")
        self.env_manager = EnvManager()
        self.env_manager.initialize_env()
        self.host_manager = HostManager()
        self.cmd_manager = CommandManager()
        self.cmd_executor = CommandExecutor()
        if self.host_manager.hosts:
            print("\033[1;32mhosts have been initialized.\033[0m")
        if self.cmd_manager.commands:
            print("\033[1;32mcommands have been initialized.\033[0m")

        MainCmd(self.env_manager,
                self.host_manager,
                self.cmd_manager,
                self.cmd_executor).cmdloop()

    def print_ascii_art():
        fonts = ['3-d','banner','big','bigchief',
                'catwalk','coinstak','colossal',
                'doom','linux','lockergnome',
                'nancyj','ntgreek','peaks','rowancap','shadow']
        random_font = random.choice(fonts)
        art = pyfiglet.figlet_format("artifactor", font=random_font).rstrip()
        art_color = 'green'
        art_line1 = 'A R T I F A C T O R'
        art_line2 = '3d6564'
        art_line3 = '3d6564@gmail.com'
        line1_color = 'yellow'
        line2_color = 'magenta'
        line3_color = 'red'
        print(colored(art, art_color) + '\n' + 
            colored(art_line1, line1_color) + '\n' +
            colored(art_line2, line2_color) + ' ' + 
            colored('(', line2_color) + 
            colored(art_line3, line3_color) + 
            colored(')', line2_color))