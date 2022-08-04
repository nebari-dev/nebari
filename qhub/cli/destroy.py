import logging
import pathlib

from qhub.destroy import destroy_configuration
from qhub.render import render_template
from qhub.schema import verify
from qhub.utils import load_yaml

logger = logging.getLogger(__name__)


def create_destroy_subcommand(subparser):
    subparser = subparser.add_parser("destroy")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.add_argument("-o", "--output", default="./", help="output directory")
    subparser.add_argument(
        "--disable-render",
        action="store_true",
        help="Disable auto-rendering before destroy",
    )
    subparser.set_defaults(func=handle_destroy)


def handle_destroy(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    config = load_yaml(config_filename)

    verify(config)

    if not args.disable_render:
        render_template(args.output, args.config, force=True)

    destroy_configuration(config)
