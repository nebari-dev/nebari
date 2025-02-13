import os
import re

import requests


def get_conda_store_session_token(username, password, nebari_hostname):
    """Log into conda-store using the test account and get session"""
    session = requests.Session()
    r = session.get(f"https://{nebari_hostname}/conda-store/login/?next=", verify=False)
    auth_url = re.search('action="([^"]+)"', r.content.decode("utf8")).group(1)
    response = session.post(
        auth_url.replace("&amp;", "&"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": username,
            "password": password,
            "credentialId": "",
        },
        verify=False,
    )
    assert response.status_code == 200

    token = session.cookies.get("conda-store-auth")
    response = requests.get(
        f"https://{nebari_hostname}/conda-store/api/v1/permission/",
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
    )
    assert response.status_code == 200

    return token


if __name__ == "__main__":
    username = os.environ.get("KEYCLOAK_USERNAME")
    password = os.environ.get("KEYCLOAK_PASSWORD")
    url = os.environ.get("BASE_URL")
    token = get_conda_store_session_token(username, password, url)
    print(token)
