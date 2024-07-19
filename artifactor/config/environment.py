import os
from dotenv import load_dotenv, dotenv_values
from utils.helpers import check_and_create_file

class EnvManager:
    def __init__(self, env_file='.env'):
        self.env_file = env_file
        self.env_vars = {
            'USE_JUMPBOX': None,
            'USE_PORT_FORWARD': None,
            'USE_JUMPBOX_PASSWORD': None,
            'USE_TARGET_PASSWORD': None,
            'JUMPBOX': None,
            'JUMPBOX_KEY': None,
            'JUMPBOX_USERNAME': None,
            'JUMPBOX_PASSWORD': None,
            'TARGET_KEY': None,
            'TARGET_USERNAME': None,
            'TARGET_PASSWORD': None,
            'WIN_USERNAME': None,
            'WIN_PASSWORD': None,
            'PING_COUNT': None,
            'PING_TIMEOUT': None
        }
        check_and_create_file(self.env_file)
        self.load_environment()

    def load_environment(self):
        self.env_vars = dotenv_values(self.env_file)

    def get_env_var(self, var_name):
        return self.env_vars[var_name]

    def set_env_var(self, var_name, var_value):
        env_vars = dotenv_values(self.env_file)
        env_vars[var_name] = var_value
        with open(self.env_file, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        self.load_environment()

    def get_or_prompt_env_var(self, var_name, prompt_text):
        value = self.get_env_var(var_name)
        if value in [None, 'None']:
            value = input(prompt_text)
            self.set_env_var(var_name, value)
        return value

    def initialize_env(self):
        self.load_environment()
        required_var_set = False

        for key in self.env_vars:
            value = self.get_env_var(key)
            if value is None:
                print(f"\033[1;31mWarning: {key} is not set in the environment file.\033[0m")
            else:
                if key == 'USE_JUMPBOX':
                    while not required_var_set:
                        value = self.get_or_prompt_env_var('USE_JUMPBOX', "Do you want to use a jumpbox? (Y/N): ").strip().upper()        
                        if value in ['Y', 'N']:
                            required_var_set = True
                            print(f"\n\033[1;32mJumpbox usage set to: {self.env_vars['USE_JUMPBOX']}\033[0m")
                        else:
                            self.set_env_var('USE_JUMPBOX', None)
                self.env_vars[key] = value

        print("\033[1;32menvironment variables have been initialized.\033[0m")