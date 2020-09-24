from os import path

from qhub.render import render_default_template, render_template
from qhub.schema import verify

def create_init_subcommand(subparser):
    subparser = subparser.add_parser("init")
    subparser.add_argument("platform", help="Cloud platform where QHub needs to deployed!", type=str)
    subparser.set_defaults(func=handle_init)


def handle_init(args):
    import pathlib
    from shutil import copyfile
    import yaml

    import qhub

    platform = args.platform
    config_dir = pathlib.Path(qhub.__file__).parent / "template/configs/"

    if platform == "aws":
        print("Generating QHub configuration for AWS")
        copyfile(path.join(config_dir, "config_aws.yaml"), "qhub-ops-config.yaml")
    elif platform == "gcp":
        print("Generating QHub configuration for GCP")
        copyfile(path.join(config_dir, "config_gcp.yaml"), "qhub-ops-config.yaml")
    elif platform == "do":
        print("Generating QHub configuration for Digital Ocean")
        copyfile(path.join(config_dir, "config_do.yaml"), "qhub-ops-config.yaml")
    elif platform == "azure":
        print("Work in Progress")
    else:
        print("Only aws | gcp | do are supported!")
