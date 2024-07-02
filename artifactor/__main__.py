# 
from app.app import Artifactor
from app.menu import print_ascii_art

if __name__ == "__main__":
    print_ascii_art()
    app = Artifactor()
    app.cmdloop()