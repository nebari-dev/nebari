import requests


def test_service_status(deploy, nebari_endpoint):
    assert (
        requests.get(
            f"https://{nebari_endpoint}/hub/api/", verify=False
        ).status_code
        == 200
    )
    assert (
        requests.get(
            f"https://{nebari_endpoint}/auth/realms/master", verify=False
        ).status_code
        == 200
    )
    assert (
        requests.get(
            f"https://{nebari_endpoint}/gateway/api/version", verify=False
        ).status_code
        == 200
    )
    assert (
        requests.get(
            f"https://{nebari_endpoint}/conda-store/api/v1/", verify=False
        ).status_code
        == 200
    )
    assert (
        requests.get(
            f"https://{nebari_endpoint}/monitoring/api/health", verify=False
        ).status_code
        == 200
    )


def test_verify_keycloak_users(deploy, nebari_config):
    """Tests if keycloak is working and it has expected users"""
    keycloak_url = f"https://{nebari_config.domain}/auth"
    password = nebari_config.security.keycloak.initial_root_password

    from keycloak import KeycloakAdmin

    keycloak_admin = KeycloakAdmin(
        server_url=keycloak_url,
        username="nebari-bot",
        password=password,
        realm_name="master",
        client_id="admin-cli",
        verify=False,
    )
    assert set([u["username"] for u in keycloak_admin.get_users()]) == {
        "nebari-bot",
        "read-only-user",
        "root",
    }
