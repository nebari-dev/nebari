from os import path


def create_init_subcommand(subparser):
    subparser = subparser.add_parser("init")
    subparser.add_argument(
        "platform", help="Cloud platform where QHub needs to deployed!", type=str
    )
    subparser.set_defaults(func=handle_init)


def handle_init(args):
    platform = args.platform
    import pathlib
    import qhub

    config_dir = pathlib.Path(qhub.__file__).parent / "template/configs/"

    if platform == "aws":
        print("Generating QHub configuration for AWS")
        generate_qhub_config(path.join(config_dir, "config_aws.yaml"))
    elif platform == "gcp":
        print("Generating QHub configuration for GCP")
        generate_qhub_config(path.join(config_dir, "config_gcp.yaml"))
    elif platform == "do":
        print("Generating QHub configuration for Digital Ocean")
        generate_qhub_config(path.join(config_dir, "config_do.yaml"))
    elif platform == "azure":
        print("Work in Progress")
    else:
        print("Only aws | gcp | do are supported!")


def generate_qhub_config(config_file, out="qhub-ops-config.yaml"):
    from shutil import copyfile

    copyfile(config_file, out)
