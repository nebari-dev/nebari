import re
import ssl

import requests

from tests.tests_deployment import constants


def get_jupyterhub_session():
    session = requests.Session()
    r = session.get(
        f"https://{constants.NEBARI_HOSTNAME}/hub/oauth_login", verify=False
    )
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


def create_jupyterhub_token(note):
    session = get_jupyterhub_session()
    xsrf_token = session.cookies.get("_xsrf")
    headers = {"Referer": f"https://{constants.NEBARI_HOSTNAME}/hub/token"}
    if xsrf_token:
        headers["X-XSRFToken"] = xsrf_token
    data = {"note": note, "expires_in": None}
    return session.post(
        f"https://{constants.NEBARI_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}/tokens",
        headers=headers,
        json=data,
        verify=False,
    )


def get_jupyterhub_token(note="jupyterhub-tests-deployment"):
    response = create_jupyterhub_token(note=note)
    return response.json()["token"]


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
