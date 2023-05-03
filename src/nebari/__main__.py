import sys

from nebari.cli.main import app


def main():
    app(sys.argv[1:])


if __name__ == "__main__":
    main()
