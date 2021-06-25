import pathlib
import logging

from ruamel import yaml

from qhub.forcedestroy import force_destroy_configuration

logger = logging.getLogger(__name__)


def create_force_destroy_subcommand(subparser):
    subparser = subparser.add_parser("force-destroy")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.set_defaults(func=handle_force_destroy)


def handle_force_destroy(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    # Don't verify(config) in case the schema has changed - just pick out the important bits and tear down

    force_destroy_configuration(config)
