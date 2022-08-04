import logging
import pathlib

from qhub.keycloak import do_keycloak

logger = logging.getLogger(__name__)


def create_keycloak_subcommand(subparser):
    subparser = subparser.add_parser("keycloak")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.add_argument(
        "keycloak_action",
        nargs="+",
        help="`adduser <username> [password]` or `listusers`",
    )
    subparser.set_defaults(func=handle_keycloak)


def handle_keycloak(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    do_keycloak(config_filename, *args.keycloak_action)
