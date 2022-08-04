import pathlib

from qhub.provider.cicd.linter import comment_on_pr
from qhub.schema import verify
from qhub.utils import load_yaml


def create_validate_subcommand(subparser):
    subparser = subparser.add_parser("validate")
    subparser.add_argument(
        "configdeprecated",
        help="qhub configuration yaml file (deprecated - please pass in as -c/--config flag)",
        nargs="?",
    )
    subparser.add_argument(
        "-c", "--config", help="qhub configuration yaml file", required=False
    )
    subparser.add_argument(
        "--enable-commenting", help="Turn on PR commenting", action="store_true"
    )
    subparser.set_defaults(func=handle_validate)


def handle_validate(args):
    if args.configdeprecated and args.config:
        raise ValueError(
            "Please pass in -c/--config flag specifying your qhub-config.yaml file, and do NOT pass it as a standalone argument"
        )

    config_filename = args.config or args.configdeprecated
    if not config_filename:
        raise ValueError(
            "Please pass in a qhub-config.yaml filename using the -c/--config argument"
        )

    config_filename = pathlib.Path(args.config or args.configdeprecated)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    config = load_yaml(config_filename)

    if args.enable_commenting:
        # for PR's only
        comment_on_pr(config)
    else:
        verify(config)
