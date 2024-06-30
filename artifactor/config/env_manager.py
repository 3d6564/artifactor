import os
from dotenv import load_dotenv, dotenv_values

class EnvManager:
    def __init__(self, env_file='.env'):
        self.env_file = env_file
        self.env_vars = {
            'USE_JUMPBOX': None,
            'USE_PORT_FORWARD': None,
            'JUMPBOX': None,
            'JUMPBOX_USERNAME': None,
            'JUMPBOX_KEY': None,
            'JUMPBOX_PASSWORD': None,
            'TARGET_USERNAME': None,
            'TARGET_KEY': None,
            'TARGET_PASSWORD': None
        }
        self.load_environment()
        self.check_and_create_env_file()

    def load_environment(self):
        load_dotenv(self.env_file, override=True)

    def check_and_create_env_file(self):
        """
        Creates empty file if none detected
        """
        if not os.path.exists(self.env_file):
            open(self.env_file, 'a').close()

    def get_env_var(self, var_name):
        return os.getenv(var_name)

    def set_env_var(self, var_name, var_value):
        env_vars = dotenv_values(self.env_file)
        env_vars[var_name] = var_value
        with open(self.env_file, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        self.load_environment()  # Reload the .env file to update the environment variables with override

    def get_or_prompt_env_var(self, var_name, prompt_text):
        value = self.get_env_var(var_name)
        if value is None:
            value = input(prompt_text)
            self.set_env_var(var_name, value)
        return value

    def set_jumpbox_use(self):
        jumpbox_use = input("Do you want to use a jumpbox? (Y/N): ").strip().upper()
        while jumpbox_use.upper() not in ["Y", "N"]:
            jumpbox_use = input("Invalid input. Do you want to use a jumpbox? (Y/N): ").strip()
        self.set_env_var('USE_JUMPBOX', jumpbox_use)
        load_dotenv(override=True)
        print(f"\n\033[1;32mJumpbox usage set to: {jumpbox_use}\033[0m")

    def initialize_env(self):
        env_vars = dotenv_values(self.env_file)
        required_var_set = False

        for key in self.env_vars:
            if key in env_vars:
                self.env_vars[key] = env_vars[key]
                os.environ[key] = env_vars[key]
                if key == 'USE_JUMPBOX' and env_vars[key] in ['Y', 'N']:
                    required_var_set = True
            else:
                print(f"\033[1;31mWarning: {key} is not set in the environment file.\033[0m")

        if not required_var_set:
            jumpbox_use = self.get_or_prompt_env_var('USE_JUMPBOX', "Do you want to use a jumpbox? (Y/N): ").strip().upper()
            while jumpbox_use not in ["Y", "N"]:
                jumpbox_use = input("Invalid input. Do you want to use a jumpbox? (Y/N): ").strip().upper()
            self.set_env_var('USE_JUMPBOX', jumpbox_use)
            print(f"\n\033[1;32mJumpbox usage set to: {jumpbox_use}\033[0m")
        else:
            print("\033[1;32mAll required environment variables have been initialized.\033[0m")