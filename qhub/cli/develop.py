import os
import sys
import tempfile

from qhub.develop import develop
from qhub.provider import git
from qhub.console import console


def create_develop_subcommand(subparser):
    subparser = subparser.add_parser("develop")
    subparser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose of logging",
    )
    subparser.add_argument(
        "--disable-build-images",
        action="store_false",
        help="disable building Docker images",
    )
    subparser.add_argument(
        "--profile",
        default="qhub",
        help="minikube profile to use for development",
    )
    subparser.add_argument(
        "--kubernetes-version",
        default="v1.20.2",
        help="kubernetes version to use for development",
    )
    subparser.add_argument(
        "--pr",
        help="develop using a specific QHub PR",
    )
    subparser.add_argument(
        "--rev",
        help="develop using a specific local git rev (commit or branch name)",
    )
    subparser.add_argument("--remote", action="store_true", help="")
    subparser.set_defaults(func=handle_develop)


def handle_develop(args):
    if args.pr or args.rev:
        if args.pr:
            branch_name = f"qhub-develop-pr-{args.pr}"
            worktree_directory = os.path.join(
                tempfile.gettempdir(), "qhub", branch_name
            )
            git.fetch(remote="origin", branch_name=f"pull/{args.pr}/head:{branch_name}")
            console.rule(f"GitHub PR {args.pr}")
        elif args.rev:
            branch_name = args.rev
            worktree_directory = os.path.join(
                tempfile.gettempdir(), "qhub", branch_name
            )
            console.rule(f"Local rev {args.rev}")

        git.worktree_add(directory=worktree_directory, branch_name=branch_name)
        os.chdir(worktree_directory)
        console.print(f"Changing directory to {worktree_directory}")

        command_args = [
            sys.executable,
            "-m",
            "qhub",
            "develop",
            "--profile",
            args.profile,
            "--kubernetes-version",
            args.kubernetes_version,
        ]

        if args.verbose:
            command_args.append("--verbose")

        if not args.disable_build_images:
            command_args.append("--disable-build-images")

        if args.remote:
            command_args.append("--remote")

        console.print(
            f'When done run "git worktree remove {branch_name} --force" to delete worktree'
        )
        console.print(f"$ {' '.join(command_args)}")
        os.execv(command_args[0], command_args)
    else:  # default is to use current working tree
        develop(
            verbose=args.verbose,
            build_images=args.disable_build_images,
            profile=args.profile,
            kubernetes_version=args.kubernetes_version,
            remote=args.remote,
        )
