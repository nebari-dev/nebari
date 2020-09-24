import argparse
import logging
import sys
from os import path

from qhub.cli.deploy import create_deploy_subcommand
from qhub.cli.initialize import create_init_subcommand
from qhub.cli.render import create_render_subcommand
from qhub.cli.validate import create_validate_subcommand

root_dir = path.abspath(path.join(path.dirname(__file__), path.pardir))

with open(path.join(root_dir, "VERSION")) as version_file:
    version = version_file.read().strip()


def cli(args):
    parser = argparse.ArgumentParser(description="QHub command line")
    parser.add_argument(
        "-v", "--version", action="version", version=version, help="QHub Ops version"
    )
    parser.set_defaults(func=None)

    subparser = parser.add_subparsers(help=f"QHub Ops - {version}")
    create_deploy_subcommand(subparser)
    create_render_subcommand(subparser)
    create_init_subcommand(subparser)
    create_validate_subcommand(subparser)

    args = parser.parse_args(args)

    if args.func is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    args.func(args)
