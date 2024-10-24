import pathlib

from _nebari.config import read_configuration
from _nebari.keycloak import get_keycloak_admin_from_config
from nebari.plugins import nebari_plugin_manager
from tests.tests_deployment import constants


def get_keycloak_client_details_by_name(client_name, keycloak_admin=None):
    if not keycloak_admin:
        keycloak_admin = get_keycloak_admin()
    clients = keycloak_admin.get_clients()
    for client in clients:
        if client["clientId"] == client_name:
            return client


def get_keycloak_user_details_by_name(username, keycloak_admin=None):
    if not keycloak_admin:
        keycloak_admin = get_keycloak_admin()
    users = keycloak_admin.get_users()
    for user in users:
        if user["username"] == username:
            return user


def get_keycloak_role_details_by_name(roles, role_name):
    for role in roles:
        if role["name"] == role_name:
            return role


def get_keycloak_admin():
    config_schema = nebari_plugin_manager.config_schema
    config_filepath = constants.NEBARI_CONFIG_PATH
    assert pathlib.Path(config_filepath).exists()
    config = read_configuration(config_filepath, config_schema)
    return get_keycloak_admin_from_config(config)


def create_keycloak_client_role(
    client_id: str, role_name: str, scopes: str, component: str
):
    keycloak_admin = get_keycloak_admin()
    keycloak_admin.create_client_role(
        client_id,
        payload={
            "name": role_name,
            "description": f"{role_name} description",
            "attributes": {"scopes": [scopes], "component": [component]},
        },
    )
    client_roles = keycloak_admin.get_client_roles(client_id=client_id)
    return get_keycloak_role_details_by_name(client_roles, role_name)


def assign_keycloak_client_role_to_user(username: str, client_name: str, role: dict):
    """Given a keycloak role and client name, assign that to the user"""
    keycloak_admin = get_keycloak_admin()
    user_details = get_keycloak_user_details_by_name(
        username=username, keycloak_admin=keycloak_admin
    )
    client_details = get_keycloak_client_details_by_name(
        client_name=client_name, keycloak_admin=keycloak_admin
    )
    keycloak_admin.assign_client_role(
        user_id=user_details["id"], client_id=client_details["id"], roles=[role]
    )


def create_keycloak_role(client_name: str, role_name: str, scopes: str, component: str):
    """Create a role keycloak role for the given client with scopes and
    component set in attributes
    """
    keycloak_admin = get_keycloak_admin()
    client_details = get_keycloak_client_details_by_name(
        client_name=client_name, keycloak_admin=keycloak_admin
    )
    return create_keycloak_client_role(
        client_details["id"], role_name=role_name, scopes=scopes, component=component
    )


def get_keycloak_client_role(client_name, role_name):
    keycloak_admin = get_keycloak_admin()
    client_details = get_keycloak_client_details_by_name(
        client_name=client_name, keycloak_admin=keycloak_admin
    )
    return keycloak_admin.get_client_role(
        client_id=client_details["id"], role_name=role_name
    )


def get_keycloak_client_roles(client_name):
    keycloak_admin = get_keycloak_admin()
    client_details = get_keycloak_client_details_by_name(
        client_name=client_name, keycloak_admin=keycloak_admin
    )
    return keycloak_admin.get_client_roles(client_id=client_details["id"])


def get_keycloak_role_groups(client_id, role_name):
    keycloak_admin = get_keycloak_admin()
    return keycloak_admin.get_client_role_groups(
        client_id=client_id, role_name=role_name
    )


def delete_client_keycloak_test_roles(client_name):
    keycloak_admin = get_keycloak_admin()
    client_details = get_keycloak_client_details_by_name(
        client_name=client_name, keycloak_admin=keycloak_admin
    )
    client_roles = keycloak_admin.get_client_roles(client_id=client_details["id"])
    for role in client_roles:
        if not role["name"].startswith("test"):
            continue
        keycloak_admin.delete_client_role(
            client_role_id=client_details["id"],
            role_name=role["name"],
        )
