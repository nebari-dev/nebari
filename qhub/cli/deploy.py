import yaml
import pathlib
import logging

from qhub.deploy import deploy_configuration
from qhub.schema import verify

logger = logging.getLogger(__name__)


def create_deploy_subcommand(subparser):
    subparser = subparser.add_parser("deploy")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.add_argument(
        "--dns-provider",
        choices=["cloudflare"],
        help="dns provider to use for registering domain name mapping",
    )
    subparser.add_argument(
        "--dns-auto-provision",
        action="store_true",
        help="Attempt to automatically provision DNS. For Auth0 is requires environment variables AUTH0_DOMAIN, AUTH0_CLIENTID, AUTH0_CLIENT_SECRET",
    )
    subparser.add_argument(
        "--disable-prompt", action="store_true", help="Disable human intervention"
    )
    subparser.set_defaults(func=handle_deploy)


def handle_deploy(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    verify(config)

    deploy_configuration(
        config, args.dns_provider, args.dns_auto_provision, args.disable_prompt
    )
