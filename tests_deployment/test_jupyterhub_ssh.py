import paramiko
import pytest

from tests_deployment import constants
from tests_deployment.utils import get_jupyterhub_token, monkeypatch_ssl_context

monkeypatch_ssl_context()


@pytest.fixture
def paramiko_object():
    """Connects to JupyterHub ssh cluster from outside the cluster."""
    api_token = get_jupyterhub_token("jupyterhub-ssh")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(
            hostname=constants.QHUB_HOSTNAME,
            port=8022,
            username=constants.KEYCLOAK_USERNAME,
            password=api_token,
            # wait 5 minutes for jupyterlab server/terminal to spin up
            auth_timeout=5 * 60,
        )
        yield client
    finally:
        client.close()


def test_simple_jupyterhub_ssh(paramiko_object):
    stdin, stdout, stderr = paramiko_object.exec_command('')

    stdin.write('''id
whoami
umask
hostname
df -h
ls -la
conda info
env
exit
''')
    print(stdout.read().decode('utf-8'))
