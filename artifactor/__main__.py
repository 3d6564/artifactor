# 
from app.app import Artifactor
from app.menu import print_ascii_art
from utils import ExitApplication

if __name__ == "__main__":
    print_ascii_art()
    try:
        Artifactor().cmdloop()
    except ExitApplication:
        'Application exited'
