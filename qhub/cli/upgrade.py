import logging
import pathlib

from qhub.upgrade import do_upgrade

logger = logging.getLogger(__name__)


def create_upgrade_subcommand(subparser):
    subparser = subparser.add_parser("upgrade")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.add_argument(
        "--attempt-fixes",
        action="store_true",
        help="Attempt to fix the config for any incompatibilities between your old and new QHub versions.",
    )
    subparser.set_defaults(func=handle_upgrade)


def handle_upgrade(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    do_upgrade(config_filename, args.attempt_fixes)
