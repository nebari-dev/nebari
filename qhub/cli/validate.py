import pathlib
import yaml

from qhub.schema import verify
from qhub.provider.cicd.linter import qhub_linter


def create_validate_subcommand(subparser):
    subparser = subparser.add_parser("validate")
    subparser.add_argument("config", help="qhub configuration")
    subparser.add_argument("--enable-commenting", help="Turn on PR commenting", func=qhub_linter)
    subparser.set_defaults(func=handle_validate)
    

def handle_validate(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    verify(config)
