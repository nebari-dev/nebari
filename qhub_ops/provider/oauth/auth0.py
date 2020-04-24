import os

from auth0.v3.management import Auth0
from auth0.v3.authentication import GetToken


DOMAIN = os.environ["AUTH0_DOMAIN"]
CLIENT_ID = os.environ["AUTH0_CLIENT_ID"]
CLIENT_SECRET = os.environ["AUTH0_CLIENT_SECRET"]


def create_client(jupyterhub_endpoint):
    get_token = GetToken(DOMAIN)
    token = get_token.client_credentials(
        CLIENT_ID, CLIENT_SECRET, "https://{}/api/v2/".format(DOMAIN)
    )
    mgmt_api_token = token["access_token"]

    auth0 = Auth0(DOMAIN, mgmt_api_token)

    credentials = auth0.clients.create(
        {
            "name": f"QHub - {jupyterhub_endpoint}",
            "description": f"QHub - {jupyterhub_endpoint}",
            "callbacks": [f"https://{jupyterhub_endpoint}/hub/oauth_callback"],
            "app_type": "regular_web",
        }
    )

    return {
        "auth0_subdomain": ".".join(DOMAIN.split(".")[:-2]),
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"],
        "scope": ["openid", "email", "profile"],
        "oauth_callback_url": f"https://{jupyterhub_endpoint}/hub/oauth_callback",
    }
