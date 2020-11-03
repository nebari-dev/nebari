from os import listdir, path
import shutil


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
        generate_qhub_config(path.join(config_dir, "aws"))
    elif platform == "gcp":
        print("Generating QHub configuration for GCP")
        generate_qhub_config(path.join(config_dir, "gcp"))
    elif platform == "do":
        print("Generating QHub configuration for Digital Ocean")
        generate_qhub_config(path.join(config_dir, "do"))
    elif platform == "azure":
        print("Work in Progress")
    else:
        print("Only aws | gcp | do are supported!")


def copytree(src, dst, symlinks=False, ignore=None):
    for item in listdir(src):
        s = path.join(src, item)
        d = path.join(dst, item)
        if path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def generate_qhub_config(config_dir, out="./"):
    copytree(config_dir, out)
