import re

import requests

from tests.tests_deployment import constants


def get_conda_store_session():
    """Log into conda-store using the test account and get session"""
    session = requests.Session()
    r = session.get(
        f"https://{constants.NEBARI_HOSTNAME}/conda-store/login/?next=", verify=False
    )
    auth_url = re.search('action="([^"]+)"', r.content.decode("utf8")).group(1)
    response = session.post(
        auth_url.replace("&amp;", "&"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": constants.KEYCLOAK_USERNAME,
            "password": constants.KEYCLOAK_PASSWORD,
            "credentialId": "",
        },
        verify=False,
    )
    assert response.status_code == 200
    return session


def get_conda_store_user_permissions():
    """Log into conda-store using the test account and get session and using the token in
    session call conda-store API to get permissions.
    """
    session = get_conda_store_session()
    token = session.cookies.get("conda-store-auth")
    response = requests.get(
        f"https://{constants.NEBARI_HOSTNAME}/conda-store/api/v1/permission/",
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
    )
    assert response.status_code == 200
    return response.json()
