import os

NEBARI_HOSTNAME = os.environ.get("NEBARI_HOSTNAME", "github-actions.nebari.dev")
NEBARI_CONFIG_PATH = os.environ.get("NEBARI_CONFIG_PATH", "nebari-config.yaml")
GATEWAY_ENDPOINT = "gateway"

KEYCLOAK_USERNAME = os.environ.get("KEYCLOAK_USERNAME", "nebari")
KEYCLOAK_PASSWORD = os.environ.get("KEYCLOAK_PASSWORD", "nebari")

PARAMIKO_SSH_ALLOW_AGENT = False
PARAMIKO_SSH_LOOK_FOR_KEYS = False
