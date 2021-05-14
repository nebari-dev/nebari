import pathlib

from ruamel import yaml

from qhub.render import render_template
from qhub.schema import verify


def create_render_subcommand(subparser):
    subparser = subparser.add_parser("render")
    subparser.add_argument("-o", "--output", default="./", help="output directory")
    subparser.add_argument(
        "-c", "--config", help="qhub configuration yaml file", required=True
    )
    subparser.set_defaults(func=handle_render)


def handle_render(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    verify(config)

    render_template(args.output, args.config, force=True)
