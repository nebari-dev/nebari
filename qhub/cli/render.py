from qhub.render import render_default_template, render_template
from qhub.schema import verify


def create_render_subcommand(subparser):
    subparser = subparser.add_parser("render")
    subparser.add_argument("-i", "--input", help="input directory")
    subparser.add_argument(
        "-f", "--force", action="store_true", help="overwrite existing files"
    )
    subparser.add_argument("-o", "--output", default="./", help="output directory")
    subparser.set_defaults(func=handle_render)


def handle_render(args):
    import pathlib
    import yaml

    config_filename = pathlib.Path("./qhub-config.yaml")
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    verify(config)

    if args.input is None:
        render_default_template(args.output, ".", force=args.force)
    else:
        render_template(args.input, args.output, ".", force=args.force)
