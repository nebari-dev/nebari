import os

NEBARI_HOSTNAME = os.environ.get("NEBARI_HOSTNAME", "github-actions.nebari.dev")
GATEWAY_ENDPOINT = "gateway"

KEYCLOAK_USERNAME = os.environ["KEYCLOAK_USERNAME"]
KEYCLOAK_PASSWORD = os.environ["KEYCLOAK_PASSWORD"]
