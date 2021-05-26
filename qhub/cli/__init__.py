import argparse
import logging
import sys
from pydantic.error_wrappers import ValidationError

from qhub.cli.deploy import create_deploy_subcommand
from qhub.cli.initialize import create_init_subcommand
from qhub.cli.render import create_render_subcommand
from qhub.cli.validate import create_validate_subcommand
from qhub.cli.destroy import create_destroy_subcommand
from qhub.provider.terraform import TerraformException
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
    create_render_subcommand(subparser)
    create_init_subcommand(subparser)
    create_validate_subcommand(subparser)
    create_destroy_subcommand(subparser)

    args = parser.parse_args(args)

    if args.func is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    if QHUB_GH_BRANCH:
        logging.info(f"Modifying for development branch {QHUB_GH_BRANCH}")

    try:
        args.func(args)
    except ValidationError as valerr:
        sys.exit(
            "Error: The schema validation of the qhub-config.yaml failed."
            " The following error message may be helpful in determining what went wrong:\n\n"
            + str(valerr)
        )
    except ValueError as ve:
        sys.exit("\nProblem encountered: " + str(ve) + "\n")
    except TerraformException:
        sys.exit("\nProblem encountered: Terraform error\n")
