import json
import logging
import os
from urllib.parse import urljoin

import keycloak
import requests
import rich

from _nebari.stages.kubernetes_ingress import CertificateEnum
from nebari import schema

logger = logging.getLogger(__name__)


def do_keycloak(config: schema.Main, *args):
    # suppress insecure warnings
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    keycloak_admin = get_keycloak_admin_from_config(config)

    if args[0] == "adduser":
        if len(args) < 2:
            raise ValueError(
                "keycloak command 'adduser' requires `username [password]`"
            )

        username = args[1]
        password = args[2] if len(args) >= 3 else None
        create_user(keycloak_admin, username, password, domain=config.domain)
    elif args[0] == "listusers":
        list_users(keycloak_admin)
    else:
        raise ValueError(f"unknown keycloak command {args[0]}")


def create_user(
    keycloak_admin: keycloak.KeycloakAdmin,
    username: str,
    password: str = None,
    groups=None,
    email=None,
    domain=None,
    enabled=True,
):
    payload = {
        "username": username,
        "groups": groups or ["/developer"],
        "email": email or f"{username}@{domain or 'example.com'}",
        "enabled": enabled,
    }
    if password:
        payload["credentials"] = [
            {"type": "password", "value": password, "temporary": False}
        ]
    else:
        rich.print(
            f"Creating user=[green]{username}[/green] without password (none supplied)"
        )
    user = keycloak_admin.create_user(payload)
    rich.print(f"Created user=[green]{username}[/green]")
    return user


def list_users(keycloak_admin: keycloak.KeycloakAdmin):
    num_users = keycloak_admin.users_count()
    print(f"{num_users} Keycloak Users")

    user_format = "{username:32} | {email:32} | {groups}"
    print(user_format.format(username="username", email="email", groups="groups"))
    print("-" * 120)

    for user in keycloak_admin.get_users():
        user_groups = [_["name"] for _ in keycloak_admin.get_user_groups(user["id"])]
        print(
            user_format.format(
                username=user["username"], email=user["email"], groups=user_groups
            )
        )


def get_keycloak_admin_from_config(config: schema.Main):
    keycloak_server_url = os.environ.get(
        "KEYCLOAK_SERVER_URL", f"https://{config.domain}/auth/"
    )

    keycloak_username = os.environ.get("KEYCLOAK_ADMIN_USERNAME", "root")
    keycloak_password = os.environ.get(
        "KEYCLOAK_ADMIN_PASSWORD", config.security.keycloak.initial_root_password
    )

    should_verify_tls = config.certificate.type != CertificateEnum.selfsigned

    try:
        keycloak_admin = keycloak.KeycloakAdmin(
            server_url=keycloak_server_url,
            username=keycloak_username,
            password=keycloak_password,
            realm_name=os.environ.get("KEYCLOAK_REALM", "nebari"),
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


def keycloak_rest_api_call(config: schema.Main = None, request: str = None):
    """Communicate directly with the Keycloak REST API by passing it a request"""
    keycloak_server_url = os.environ.get(
        "KEYCLOAK_SERVER_URL", f"https://{config.domain}/auth/"
    )

    keycloak_admin_username = os.environ.get("KEYCLOAK_ADMIN_USERNAME", "root")
    keycloak_admin_password = os.environ.get(
        "KEYCLOAK_ADMIN_PASSWORD",
        config.security.keycloak.initial_root_password,
    )

    try:
        # Get `token` to interact with Keycloak Admin
        url = urljoin(
            keycloak_server_url, "realms/master/protocol/openid-connect/token"
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "username": keycloak_admin_username,
            "password": keycloak_admin_password,
            "grant_type": "password",
            "client_id": "admin-cli",
        }

        response = requests.post(
            url=url,
            headers=headers,
            data=data,
            verify=False,
        )

        if response.status_code == 200:
            token = json.loads(response.content.decode())["access_token"]
        else:
            raise ValueError(
                f"Unable to retrieve Keycloak API token. Status code: {response.status_code}"
            )

        # Send request to Keycloak REST API
        method, endpoint = request.split()
        url = urljoin(
            urljoin(keycloak_server_url, "admin/realms/"), endpoint.lstrip("/")
        )
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

        response = requests.request(
            method=method, url=url, headers=headers, verify=False
        )

        if response.status_code == 200:
            content = json.loads(response.content.decode())
            return content
        else:
            raise ValueError(
                f"Unable to communicate with Keycloak API. Status code: {response.status_code}"
            )

    except requests.exceptions.RequestException as e:
        raise e


def export_keycloak_users(config: schema.Main, realm: str):
    request = f"GET /{realm}/users"

    users = keycloak_rest_api_call(config, request=request)

    return {
        "realm": realm,
        "users": users,
    }
