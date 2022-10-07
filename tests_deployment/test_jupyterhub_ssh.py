import re
import uuid

import paramiko
import pytest

from tests_deployment import constants
from tests_deployment.utils import (
    escape_string,
    get_jupyterhub_token,
    monkeypatch_ssl_context,
)

monkeypatch_ssl_context()

TIMEOUT_SECS = 300


@pytest.fixture
def paramiko_object():
    """Connects to JupyterHub ssh cluster from outside the cluster."""
    api_token = get_jupyterhub_token("jupyterhub-ssh")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(
            hostname=constants.NEBARI_HOSTNAME,
            port=8022,
            username=constants.KEYCLOAK_USERNAME,
            password=api_token,
            # wait 5 minutes for jupyterlab server/terminal to spin up
            auth_timeout=5 * 60,
        )
        yield client
    finally:
        client.close()


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
def test_simple_jupyterhub_ssh(paramiko_object):
    stdin, stdout, stderr = paramiko_object.exec_command("")


@pytest.mark.timeout(TIMEOUT_SECS)
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
        ("hostname", f"jupyter-{escape_string(constants.KEYCLOAK_USERNAME)}"),
    ]

    for command, output in commands_exact:
        assert output == run_command(command, stdin, stdout, stderr)


@pytest.mark.timeout(TIMEOUT_SECS)
def test_contains_jupyterhub_ssh(paramiko_object):
    stdin, stdout, stderr = paramiko_object.exec_command("")

    # commands to run and string need to be contained in output
    commands_contain = [
        ("ls -la", ".bashrc"),
        ("ls -la /shared/examples", "dashboard_panel.ipynb"),
        ("cat ~/.bashrc", "Managed by QHub"),
        ("cat ~/.profile", "Managed by QHub"),
        ("cat ~/.bash_logout", "Managed by QHub"),
    ]

    for command, output in commands_contain:
        assert output in run_command(command, stdin, stdout, stderr)
