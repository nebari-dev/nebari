import argparse
import logging
import sys

from pydantic.error_wrappers import ValidationError

from nebari.cli.cost import create_cost_subcommand
from nebari.cli.deploy import create_deploy_subcommand
from nebari.cli.destroy import create_destroy_subcommand
from nebari.cli.initialize import create_init_subcommand
from nebari.cli.keycloak import create_keycloak_subcommand
from nebari.cli.render import create_render_subcommand
from nebari.cli.support import create_support_subcommand
from nebari.cli.upgrade import create_upgrade_subcommand
from nebari.cli.validate import create_validate_subcommand
from nebari.provider.terraform import TerraformException
from nebari.version import __version__


def cli(args):
    parser = argparse.ArgumentParser(description="nebari command line")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
        help="nebari version number",
    )
    parser.set_defaults(func=None)

    subparser = parser.add_subparsers(help=f"nebari - {__version__}")
    create_deploy_subcommand(subparser)
    create_render_subcommand(subparser)
    create_init_subcommand(subparser)
    create_validate_subcommand(subparser)
    create_destroy_subcommand(subparser)
    create_support_subcommand(subparser)
    create_upgrade_subcommand(subparser)
    create_keycloak_subcommand(subparser)
    create_cost_subcommand(subparser)

    args = parser.parse_args(args)

    if args.func is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    try:
        args.func(args)
    except ValidationError as valerr:
        sys.exit(
            "Error: The schema validation of the nebari-config.yaml failed."
            " The following error message may be helpful in determining what went wrong:\n\n"
            + str(valerr)
        )
    except ValueError as ve:
        sys.exit("\nProblem encountered: " + str(ve) + "\n")
    except TerraformException:
        sys.exit("\nProblem encountered: Terraform error\n")
