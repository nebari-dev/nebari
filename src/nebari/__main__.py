import sys

from _nebari.cli.main import app as nebari

if __name__ == "__main__":
    nebari(sys.argv[1:])
