import pathlib

from ruamel import yaml

from qhub.schema import verify


def create_validate_subcommand(subparser):
    subparser = subparser.add_parser("validate")
    subparser.add_argument("config", help="qhub configuration")
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
