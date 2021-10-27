from qhub.develop import develop


def create_develop_subcommand(subparser):
    subparser = subparser.add_parser("develop")
    subparser.add_argument(
        "-v", "--verbose", action="store_true", help="verbose of logging",
    )
    subparser.add_argument(
        "--disable-build-images", action="store_false", help="disable building Docker images",
    )
    subparser.add_argument(
        "--profile", default="qhub", help="minikube profile to use for development",
    )
    subparser.add_argument(
        "--kubernetes-version", default="v1.20.2", help="kubernetes version to use for development",
    )
    subparser.add_argument(
        "--remote", action="store_true", help=""
    )
    subparser.set_defaults(func=handle_develop)


def handle_deploy(args):
    develop(
        verbose=args.verbose,
        build_images=args.disable_build_images,
        profile=args.profile,
        kubernetes_version=args.kubernetes_version,
        remote=args.remote)
