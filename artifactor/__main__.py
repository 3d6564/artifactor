# 
from app.app import Artifactor
from utils import ExitApplication

if __name__ == "__main__":
    Artifactor.print_ascii_art()
    try:
        Artifactor()
    except ExitApplication:
        'Application exited'
