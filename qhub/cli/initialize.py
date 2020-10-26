from os import path
import secrets


def create_init_subcommand(subparser):
    subparser = subparser.add_parser("init")
    subparser.add_argument(
        "platform", help="Cloud platform where QHub needs to deployed!",
        type=str, choices=['do', 'gcp', 'aws',
    )
    subparser.add_argument(
        '--project', help='Namespace to assign to qhub resources'
    )
    subparser.add_argument(
        '--domain', help='Domain for jupyterhub clister to be deployed under'
    )
    subparser.add_argument(
        '--ci--provider', choices=['github-actions'],
        help='continuous integration to use for infrastructure as code'
    )
    subparser.add_argument(
        '--oauth--provider', choices=['github', 'auth0'],
        default='github',
        help='oauth provider to use for authentication'
    )
    subparser.add_argument(
        '--oauth-provision', action='store_true',
        help='If true init will attempt to automatically provision oauth. Required environment variables AUTH0_CLIENTID, AUTH0_CLIENT_SECRET',
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


def generate_qhub_config(config_file, out="qhub-config.yaml"):
    from shutil import copyfile

    copyfile(config_file, out)
