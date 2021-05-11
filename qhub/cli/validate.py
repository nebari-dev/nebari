import pathlib

from ruamel import yaml

from qhub.schema import verify
from qhub.provider.cicd.linter import comment_on_pr


def create_validate_subcommand(subparser):
    subparser = subparser.add_parser("validate")
    subparser.add_argument("config", help="qhub configuration")
    subparser.add_argument(
        "--enable-commenting", help="Turn on PR commenting", action="store_true"
    )
    subparser.set_defaults(func=handle_validate)


def handle_validate(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    if args.enable_commenting:
        # for PR's only
        comment_on_pr(config)
    else:
        verify(config)
