import ssl
import re

import requests

from tests_deployment import constants


def get_jupyterhub_session():
    session = requests.Session()
    r = session.get(f"https://{constants.QHUB_HOSTNAME}/hub/oauth_login", verify=False)
    auth_url = re.search('action="([^"]+)"', r.content.decode("utf8")).group(1)

    r = session.post(
        auth_url.replace("&amp;", "&"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": constants.KEYCLOAK_USERNAME,
            "password": constants.KEYCLOAK_PASSWORD,
            "credentialId": "",
        },
        verify=False,
    )
    return session


def get_jupyterhub_token():
    session = get_jupyterhub_session()
    r = session.post(
        f"https://{constants.QHUB_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}/tokens",
        headers={
            "Referer": f"https://{constants.QHUB_HOSTNAME}/hub/token",
        },
        json={
            "note": "qhub deployment test token",
            "expires_in": None,
        },
    )
    return r.json()["token"]


def monkeypatch_ssl_context():
    """
    This is a workaround monkeypatch to disable ssl checking to avoid SSL
    failures.
    TODO: A better way to do this would be adding the Traefik's default certificate's
    CA public key to the trusted certificate authorities.
    """

    def create_default_context(context):
        def _inner(*args, **kwargs):
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context

        return _inner

    sslcontext = ssl.create_default_context()
    ssl.create_default_context = create_default_context(sslcontext)
