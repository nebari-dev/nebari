import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Dict, List
from urllib.parse import urljoin

import keycloak
import requests
import rich
import urllib3

from _nebari.stages.kubernetes_ingress import CertificateEnum
from nebari import schema

logger = logging.getLogger(__name__)


def do_keycloak() -> Callable:
    """
    A simple decorator *factory* to wrap functions that interact with Keycloak. Injects
    the config parameter depending on the function signature and expects the presence of
    the keycloak_admin parameter in the wrapped function.

    Usage:
        @do_keycloak()
        def keycloak_list_users(keycloak_admin):
            ...
        user = keycloak_list_users(config)
    """

    def _decorator(func: Callable) -> Callable:
        @wraps(func)
        def _wrapper(config, *args, **kwargs):
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            keycloak_admin = get_keycloak_admin_from_config(config=config)

            return func(keycloak_admin, *args, **kwargs)

        return _wrapper

    return _decorator


@do_keycloak()
def create_user(
    keycloak_admin: keycloak.KeycloakAdmin,
    username: str,
    password: str = None,
    groups: list = None,
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
    if groups:
        _available_group_names = [_["name"] for _ in keycloak_admin.get_groups()]
        if not all([_ in _available_group_names for _ in groups]):
            raise ValueError(f"Keycloak group(s) not found: {groups}")
    else:
        rich.print(
            f"Creating user=[green]{username}[/green] without password (none supplied)"
        )
    user = keycloak_admin.create_user(payload)
    rich.print(f"Created user=[green]{username}[/green]")
    return user


@do_keycloak()
def list_users(keycloak_admin: keycloak.KeycloakAdmin) -> Dict[str, Any]:
    """
    Return a list of user info from Keycloak, including username, email, and groups.
    """
    return {
        "count": keycloak_admin.users_count(),
        "users": [
            {
                "username": user["username"],
                "email": user["email"],
                "groups": [
                    group["name"]
                    for group in keycloak_admin.get_user_groups(user["id"])
                ],
            }
            for user in keycloak_admin.get_users()
        ],
    }


def get_expected_roles(expected_roles, group_name):
    return [
        role
        for client, roles in expected_roles.items()
        for role in roles
        if not (client == "realm-management" and group_name != "superadmin")
    ]


@do_keycloak()
def list_groups(keycloak_admin: keycloak.KeycloakAdmin) -> List[Dict[str, Any]]:
    """Return a list of group info from Keycloak, excluding 'realm-management' roles for all groups except 'superadmin'."""
    groups_data = []
    for group in keycloak_admin.get_groups():
        attrs = keycloak_admin.get_group_by_path(group["path"])
        client_roles = attrs.get("clientRoles", {})

        # Collect roles except 'realm-management' (unless group is 'superadmin')
        roles = get_expected_roles(client_roles, group_name=group["name"])

        groups_data.append(
            {
                "name": group["name"],
                "roles": roles,
            }
        )

    return groups_data


def get_keycloak_admin(server_url, username, password, verify=False):
    try:
        keycloak_admin = keycloak.KeycloakAdmin(
            server_url=server_url,
            username=username,
            password=password,
            realm_name=os.environ.get("KEYCLOAK_REALM", "nebari"),
            user_realm_name="master",
            auto_refresh_token=("get", "put", "post", "delete"),
            verify=verify,
        )
    except (
        keycloak.exceptions.KeycloakConnectionError,
        keycloak.exceptions.KeycloakAuthenticationError,
    ) as e:
        raise ValueError(f"Failed to connect to Keycloak server: {e}")

    return keycloak_admin


def get_keycloak_admin_from_config(config: schema.Main):
    keycloak_server_url = os.environ.get(
        "KEYCLOAK_SERVER_URL", f"https://{config.domain}/auth/"
    )

    keycloak_username = os.environ.get("KEYCLOAK_ADMIN_USERNAME", "root")
    keycloak_password = os.environ.get(
        "KEYCLOAK_ADMIN_PASSWORD", config.security.keycloak.initial_root_password
    )

    should_verify_tls = config.certificate.type != CertificateEnum.selfsigned

    return get_keycloak_admin(
        server_url=keycloak_server_url,
        username=keycloak_username,
        password=keycloak_password,
        verify=should_verify_tls,
    )


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
