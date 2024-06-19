import os
from dotenv import load_dotenv, dotenv_values

class EnvManager:
    def __init__(self):
        load_dotenv(override=True)
        self.check_and_create_env_file()

    def check_and_create_env_file(self):
        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                pass

    def get_env_var(self, var_name):
        return os.getenv(var_name)

    def set_env_var(self, var_name, var_value):
        env_vars = dotenv_values(".env")
        env_vars[var_name] = var_value
        with open(".env", "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        load_dotenv(override=True)  # Reload the .env file to update the environment variables with override

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