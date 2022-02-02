import logging
import os

import keycloak

from .schema import verify
from .utils import load_yaml

logger = logging.getLogger(__name__)


def do_keycloak(config_filename, *args):
    keycloak_admin = get_keycloak_admin_from_config(config_filename)

    if args[0] == "adduser":
        if len(args) < 2:
            raise ValueError(
                "keycloak command 'adduser' requires `username [password]`"
            )

        username = args[1]
        password = args[2] if len(args) >= 3 else None
        create_user(keycloak_admin, username, password)
    elif args[0] == "listusers":
        list_users(keycloak_admin)
    else:
        raise ValueError(f"unknown keycloak command {args[0]}")


def create_user(
    keycloak_admin: keycloak.KeycloakAdmin,
    username: str,
    password: str = None,
    groups=None,
    enabled=True,
):
    payload = {
        "username": username,
        "groups": groups or ["/developer"],
        "enabled": enabled,
    }
    if password:
        payload["credentials"] = [
            {"type": "password", "value": password, "temporary": False}
        ]
    else:
        print(f"Creating user={username} without password (none supplied)")
    keycloak_admin.create_user(payload)


def list_users(keycloak_admin: keycloak.KeycloakAdmin):
    # supress insecure warnings
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    num_users = keycloak_admin.users_count()
    print(f"{num_users} Keycloak Users")

    user_format = "{username:32} | {groups}"
    print(user_format.format(username="username", groups="groups"))
    print("-" * 80)

    for user in keycloak_admin.get_users():
        user_groups = [_["name"] for _ in keycloak_admin.get_user_groups(user["id"])]
        print(user_format.format(username=user["username"], groups=user_groups))


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
            realm_name=os.environ.get(
                "KEYCLOAK_REALM", f"qhub-{config['project_name']}"
            ),
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
