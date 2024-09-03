import re
import string
import uuid

import paramiko
import pytest

from _nebari.utils import escape_string
from tests.tests_deployment import constants
from tests.tests_deployment.utils import monkeypatch_ssl_context

monkeypatch_ssl_context()

TIMEOUT_SECS = 300


@pytest.fixture(scope="function")
def paramiko_object(jupyterhub_access_token):
    """Connects to JupyterHub ssh cluster from outside the cluster."""
    params = {
        "hostname": constants.NEBARI_HOSTNAME,
        "port": 8022,
        "username": constants.KEYCLOAK_USERNAME,
        "password": jupyterhub_access_token,
        "allow_agent": constants.PARAMIKO_SSH_ALLOW_AGENT,
        "look_for_keys": constants.PARAMIKO_SSH_LOOK_FOR_KEYS,
        "auth_timeout": 5 * 60,
    }

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(**params)
        yield ssh_client
    finally:
        ssh_client.close()


def run_command(command, stdin, stdout, stderr):
    delimiter = uuid.uuid4().hex
    stdin.write(f"echo {delimiter}start; {command}; echo {delimiter}end\n")

    output = []

    line = stdout.readline()
    while not re.match(f"^{delimiter}start$", line.strip()):
        line = stdout.readline()

    line = stdout.readline()
    if delimiter not in line:
        output.append(line)

    while not re.match(f"^{delimiter}end$", line.strip()):
        line = stdout.readline()
        if delimiter not in line:
            output.append(line)

    return "".join(output).strip()


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_simple_jupyterhub_ssh(paramiko_object):
    stdin, stdout, stderr = paramiko_object.exec_command("")


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_print_jupyterhub_ssh(paramiko_object):
    stdin, stdout, stderr = paramiko_object.exec_command("")

    # commands to run and just print the output
    commands_print = [
        "id",
        "env",
        "conda info",
        "df -h",
        "ls -la",
        "umask",
    ]

    for command in commands_print:
        print(f'COMMAND: "{command}"')
        print(run_command(command, stdin, stdout, stderr))


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_exact_jupyterhub_ssh(paramiko_object):
    stdin, stdout, stderr = paramiko_object.exec_command("")

    # commands to run and exactly match output
    commands_exact = [
        ("id -u", "1000"),
        ("id -g", "100"),
        ("whoami", constants.KEYCLOAK_USERNAME),
        ("pwd", f"/home/{constants.KEYCLOAK_USERNAME}"),
        ("echo $HOME", f"/home/{constants.KEYCLOAK_USERNAME}"),
        ("conda activate default && echo $CONDA_PREFIX", "/opt/conda/envs/default"),
        (
            "hostname",
            f"jupyter-{escape_string(constants.KEYCLOAK_USERNAME, safe=set(string.ascii_lowercase + string.digits), escape_char='-').lower()}",
        ),
    ]

    for command, output in commands_exact:
        assert output == run_command(command, stdin, stdout, stderr)


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_contains_jupyterhub_ssh(paramiko_object):
    stdin, stdout, stderr = paramiko_object.exec_command("")

    # commands to run and string need to be contained in output
    commands_contain = [
        ("ls -la", ".bashrc"),
        ("cat ~/.bashrc", "Managed by Nebari"),
        ("cat ~/.profile", "Managed by Nebari"),
        ("cat ~/.bash_logout", "Managed by Nebari"),
        # ensure we don't copy over extra files from /etc/skel in init container
        ("ls -la ~/..202*", "No such file or directory"),
        ("ls -la ~/..data", "No such file or directory"),
    ]

    for command, output in commands_contain:
        assert output in run_command(command, stdin, stdout, stderr)
