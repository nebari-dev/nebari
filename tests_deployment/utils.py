import base64
import ssl

from kubernetes import client, config

from tests_deployment import constants


def get_kubernetes_api_instance():
    """Returns the v1 core Kubernetes api instance for making
    calls to the kubernetes cluster
    """
    config.load_kube_config()
    return client.CoreV1Api()


def get_jupyterhub_token():
    """
    It fetches the secret that has the JupyterHub token to be able to
    connect to dask gateway.
    """
    v1 = get_kubernetes_api_instance()
    secret = str(v1.read_namespaced_secret(
        constants.DASK_GATEWAY_JUPYTER_SECRET_NAME, constants.NAMESPACE
    ).data)
    base64_encoded_token = eval(secret)[constants.JUPYTERHUB_TOKEN_SECRET_KEY_NAME]
    return base64.b64decode(base64_encoded_token).decode()


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
