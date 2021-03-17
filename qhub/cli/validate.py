import pathlib
import yaml

from qhub.schema import verify
from qhub.provider.cicd.linter import qhub_linter


def create_validate_subcommand(subparser):
    subparser = subparser.add_parser("validate")
    subparser.add_argument("config", help="qhub configuration")
    subparser.set_defaults(func=handle_validate)

    linter_parser = subparser.add_parser("linter")
    linter_parser.add_argument(
        "--enable-commenting", help="Turn on PR commenting")
    linter_parser.set_defaults(func=qhub_linter)


def handle_validate(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    verify(config)
