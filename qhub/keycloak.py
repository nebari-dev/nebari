import logging
import os

import keycloak

from .schema import verify
from .utils import load_yaml

logger = logging.getLogger(__name__)


def do_keycloak(config_filename, *args):

    if len(args) < 2:
        raise ValueError("keycloak command requires extra inputs")

    if args[0] != "adduser":
        raise ValueError(
            "Only keycloak command is 'keycloak adduser username [password]'"
        )

    keycloak_admin = get_keycloak_admin_from_config(config_filename)

    new_user_dict = {"username": args[1], "enabled": True}
    if len(args) >= 3:
        new_user_dict["credentials"] = [
            {"type": "password", "value": args[2], "temporary": False}
        ]
    else:
        print("Not setting any password (none supplied)")

    print(f"Adding user {args[1]}")
    keycloak_admin.create_user(new_user_dict)


def get_keycloak_admin_from_config(config_filename):
    config = load_yaml(config_filename)

    verify(config)

    keycloak_server_url = os.environ.get(
        "KEYCLOAK_SERVER_URL", f"https://{config['domain']}/auth/"
    )

    keycloak_username = os.environ.get("KEYCLOAK_ADMIN_USERNAME", "root")
    keycloak_password = os.environ.get(
        "KEYCLOAK_ADMIN_PASSWORD",
        config.get("security", {}).get("keycloak", {}).get("initial_root_password", ""),
    )

    should_verify_tls = config.get("certificate", {}).get("type", "") != "self-signed"

    try:
        keycloak_admin = keycloak.KeycloakAdmin(
            server_url=keycloak_server_url,
            username=keycloak_username,
            password=keycloak_password,
            realm_name=os.environ.get("KEYCLOAK_REALM", "qhub"),
            user_realm_name="master",
            auto_refresh_token=("get", "put", "post", "delete"),
            verify=should_verify_tls,
        )
    except (
        keycloak.exceptions.KeycloakConnectionError,
        keycloak.exceptions.KeycloakAuthenticationError,
    ) as e:
        raise ValueError(f"Failed to connect to Keycloak server: {e}")

    return keycloak_admin
