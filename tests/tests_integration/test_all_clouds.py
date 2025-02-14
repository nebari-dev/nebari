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


def test_verify_keycloak_users(deploy):
    """Tests if keycloak is working and it has expected users"""
    keycloak_credentials = deploy["stages/05-kubernetes-keycloak"]["keycloak_credentials"]["value"]
    from keycloak import KeycloakAdmin

    keycloak_admin = KeycloakAdmin(
        server_url=f"{keycloak_credentials['url']}/auth/",
        username=keycloak_credentials["username"],
        password=keycloak_credentials["password"],
        realm_name=keycloak_credentials["realm"],
        client_id=keycloak_credentials["client_id"],
        verify=False,
    )
    assert set([u["username"] for u in keycloak_admin.get_users()]) == {
        "nebari-bot",
        "read-only-user",
        "root",
    }
