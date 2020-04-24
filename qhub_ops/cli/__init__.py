import argparse
import sys
import logging

from qhub_ops.cli.deploy import create_deploy_subcommand


def cli(args):
    parser = argparse.ArgumentParser(description="QHub command line")
    parser.set_defaults(func=None)
    create_deploy_subcommand(parser)
    args = parser.parse_args(args)

    if args.func is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    args.func(args)
