import argparse
import logging
import sys

from qhub.cli.deploy import create_deploy_subcommand
from qhub.cli.develop import create_develop_subcommand
from qhub.cli.initialize import create_init_subcommand
from qhub.cli.render import create_render_subcommand
from qhub.cli.validate import create_validate_subcommand
from qhub.cli.destroy import create_destroy_subcommand
from qhub.cli.upgrade import create_upgrade_subcommand
from qhub.utils import console, QHubError
from qhub.version import __version__
from qhub.utils import QHUB_GH_BRANCH


def cli(args):
    parser = argparse.ArgumentParser(description="QHub command line")
    parser.add_argument(
        "-v", "--version", action="version", version=__version__, help="QHub version"
    )
    parser.set_defaults(func=None)

    subparser = parser.add_subparsers(help=f"QHub - {__version__}")
    create_deploy_subcommand(subparser)
    create_develop_subcommand(subparser)
    create_render_subcommand(subparser)
    create_init_subcommand(subparser)
    create_validate_subcommand(subparser)
    create_destroy_subcommand(subparser)
    create_upgrade_subcommand(subparser)

    args = parser.parse_args(args)

    if args.func is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    if QHUB_GH_BRANCH:
        logging.info(f"Modifying for development branch {QHUB_GH_BRANCH}")

    try:
        args.func(args)
    except QHubError as qhub_error:
        console.print(qhub_error.args[0], style="red")
        sys.exit(1)
    except Exception:
        # Any Exception that does not Derive from QHubError
        # is an unhandled error within QHub and is an Error
        console.print_exception(show_locals=True)
        console.print(
            "Uncaught QHub exception encountered\n"
            "This is a bug please report with the stack trace to https://github.com/quansight/qhub/issues\n",
            style="red",
        )
        sys.exit(1)
