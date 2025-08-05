def test_verify_keycloak_users(deploy):
    """Tests if keycloak is working and it has expected users"""
    keycloak_credentials = deploy["stages/05-kubernetes-keycloak"][
        "keycloak_credentials"
    ]["value"]
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
