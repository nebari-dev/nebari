import argparse
import sys
import logging

from qhub_ops.cli.deploy import create_deploy_subcommand
from qhub_ops.cli.render import create_render_subcommand


def cli(args):
    parser = argparse.ArgumentParser(description="QHub command line")
    parser.set_defaults(func=None)

    subparser = parser.add_subparsers(help="QHub Ops")
    create_deploy_subcommand(subparser)
    create_render_subcommand(subparser)

    args = parser.parse_args(args)

    if args.func is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    args.func(args)
