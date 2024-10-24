import re
import ssl

import requests
import requests.cookies

from tests.tests_deployment import constants


def get_jupyterhub_session():
    session = requests.Session()
    session.cookies.clear()

    try:
        response = session.get(
            f"https://{constants.NEBARI_HOSTNAME}/hub/oauth_login", verify=False
        )
        response.raise_for_status()

        # Extract the authentication URL from the response
        auth_url_match = re.search('action="([^"]+)"', response.content.decode("utf8"))

        if not auth_url_match:
            raise ValueError("Authentication URL not found in response.")

        auth_url = auth_url_match.group(1).replace("&amp;", "&")

        auth_data = {
            "username": constants.KEYCLOAK_USERNAME,
            "password": constants.KEYCLOAK_PASSWORD,
            "credentialId": "",
        }
        response = session.post(
            auth_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=auth_data,
            verify=False,
        )
        response.raise_for_status()

    except requests.RequestException as e:
        raise ValueError(f"An error occurred during authentication: {e}")

    return session


def create_jupyterhub_token(note):
    session = get_jupyterhub_session()

    try:
        # Retrieve the XSRF token from session cookies
        xsrf_token = session.cookies.get("_xsrf")
    except requests.cookies.CookieConflictError:
        xsrf_token = session.cookies.get("_xsrf", path="/hub/")

    if not xsrf_token:
        raise ValueError("XSRF token not found in session cookies.")

    headers = {
        "Referer": f"https://{constants.NEBARI_HOSTNAME}/hub/token",
        "X-XSRFToken": xsrf_token,
    }

    url = f"https://{constants.NEBARI_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}/tokens"
    payload = {"note": note, "expires_in": None}

    try:
        response = session.post(url, headers=headers, json=payload, verify=False)
        if response.status_code == 403:
            # Retry with refreshed XSRF token if initial attempt is forbidden
            xsrf_token = response.cookies.get("_xsrf")
            headers["X-XSRFToken"] = xsrf_token
            response = session.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to create JupyterHub token: {e}")

    return response


def get_refresh_jupyterhub_token(old_token, note):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {old_token}",
    }

    data = {"note": note, "expires_in": None}

    try:
        response = requests.post(
            f"https://{constants.NEBARI_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}/tokens",
            headers=headers,
            json=data,
            verify=False,
        )
        response.raise_for_status()  # Ensure the request was successful

    except requests.exceptions.RequestException as e:
        raise ValueError(f"An error occurred while creating the token: {e}")

    return response


def get_jupyterhub_token(note="jupyterhub-tests-deployment"):
    response = create_jupyterhub_token(note=note)
    try:
        token = response.json()["token"]
    except (KeyError, ValueError) as e:
        print(f"An error occurred while retrieving the token: {e}")
        raise

    return token


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
