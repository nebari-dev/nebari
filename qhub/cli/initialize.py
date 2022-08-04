from qhub.initialize import render_config
from qhub.schema import ProviderEnum
from qhub.utils import QHUB_DASK_VERSION, QHUB_IMAGE_TAG, yaml


def create_init_subcommand(subparser):
    subparser = subparser.add_parser("init")
    subparser.add_argument(
        "platform",
        help="Cloud to deploy qhub on",
        type=str,
        choices=[_.value for _ in ProviderEnum],
    )
    subparser.add_argument("--project", help="Name to assign to qhub resources")
    subparser.add_argument(
        "--namespace", default="dev", help="Namespace to assign to qhub resources"
    )
    subparser.add_argument(
        "--domain",
        help="Domain for jupyterhub cluster to be deployed under",
    )
    subparser.add_argument(
        "--ci-provider",
        choices=["github-actions", "gitlab-ci", "none"],
        help="continuous integration to use for infrastructure as code",
    )
    subparser.add_argument(
        "--auth-provider",
        choices=["github", "auth0", "password"],
        default="github",
        help="auth provider to use for authentication",
    )
    subparser.add_argument("--repository", help="Repository to initialize qhub")
    subparser.add_argument(
        "--repository-auto-provision",
        action="store_true",
        help="Attempt to automatically provision repository. For github it requires environment variables GITHUB_USERNAME, GITHUB_TOKEN",
    )
    subparser.add_argument(
        "--auth-auto-provision",
        action="store_true",
        help="Attempt to automatically provision authentication. For Auth0 it requires environment variables AUTH0_DOMAIN, AUTH0_CLIENTID, AUTH0_CLIENT_SECRET",
    )
    subparser.add_argument(
        "--terraform-state",
        choices=["remote", "local", "existing"],
        default="remote",
        help="Terraform state to be provisioned and stored remotely, locally on the filesystem, or using existing terraform state backend",
    )
    subparser.add_argument(
        "--kubernetes-version",
        type=str,
        help="kubernetes version to use for cloud deployment",
    )
    subparser.add_argument(
        "--disable-prompt",
        action="store_true",
        help="Never prompt user for input instead leave PLACEHOLDER",
    )
    subparser.add_argument(
        "--ssl-cert-email",
        help="Allow generation of a LetsEncrypt SSL cert - requires an administrative email",
    )
    subparser.set_defaults(func=handle_init)


def handle_init(args):

    if QHUB_IMAGE_TAG:
        print(
            f"Modifying the image tags for the `default_images`, setting tags equal to: {QHUB_IMAGE_TAG}"
        )

    if QHUB_DASK_VERSION:
        print(
            f"Modifying the version of the `qhub_dask` package, setting version equal to: {QHUB_DASK_VERSION}"
        )

    config = render_config(
        project_name=args.project,
        namespace=args.namespace,
        qhub_domain=args.domain,
        cloud_provider=args.platform,
        ci_provider=args.ci_provider,
        repository=args.repository,
        repository_auto_provision=args.repository_auto_provision,
        auth_provider=args.auth_provider,
        auth_auto_provision=args.auth_auto_provision,
        terraform_state=args.terraform_state,
        kubernetes_version=args.kubernetes_version,
        disable_prompt=args.disable_prompt,
        ssl_cert_email=args.ssl_cert_email,
    )

    try:
        with open("qhub-config.yaml", "x") as f:
            yaml.dump(config, f)
    except FileExistsError:
        raise ValueError(
            "A qhub-config.yaml file already exists. Please move or delete it and try again."
        )
