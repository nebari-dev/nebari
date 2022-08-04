import pathlib

from qhub.render import render_template
from qhub.schema import verify
from qhub.utils import QHUB_GH_BRANCH, load_yaml


def create_render_subcommand(subparser):
    subparser = subparser.add_parser("render")
    subparser.add_argument("-o", "--output", default="./", help="output directory")
    subparser.add_argument(
        "-c", "--config", help="qhub configuration yaml file", required=True
    )
    subparser.add_argument(
        "--dry-run",
        action="store_true",
        help="simulate rendering files without actually writing or updating any files",
    )
    subparser.set_defaults(func=handle_render)


def handle_render(args):

    if QHUB_GH_BRANCH:
        print(
            f"Modifying the version of `qhub` used by git-ops workflows, installing `qhub` from branch: {QHUB_GH_BRANCH}"
        )

    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    config = load_yaml(config_filename)

    verify(config)

    render_template(args.output, args.config, force=True, dry_run=args.dry_run)
