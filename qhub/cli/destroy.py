import pathlib
import logging

from ruamel import yaml

from qhub.destroy import destroy_configuration
from qhub.schema import verify

logger = logging.getLogger(__name__)


def create_destroy_subcommand(subparser):
    subparser = subparser.add_parser("destroy")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.set_defaults(func=handle_destroy)


def handle_destroy(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    verify(config)

    destroy_configuration(config)
