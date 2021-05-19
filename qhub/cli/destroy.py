import pathlib
import logging

from ruamel import yaml

from qhub.destroy import destroy_configuration
from qhub.schema import verify
from qhub.render import render_template

logger = logging.getLogger(__name__)


def create_destroy_subcommand(subparser):
    subparser = subparser.add_parser("destroy")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.add_argument("-o", "--output", default="./", help="output directory")
    subparser.add_argument(
        "--skip-remote-state-provision",
        action="store_true",
        help="Skip terraform state import and destroy",
    )
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

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    verify(config)

    if not args.disable_render:
        render_template(args.output, args.config, force=True)

    destroy_configuration(
        config,
        args.skip_remote_state_provision,
    )
