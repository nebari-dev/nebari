import sys

from _nebari.cli.main import app


def main():
    app(sys.argv[1:])


if __name__ == "__main__":
    main()
