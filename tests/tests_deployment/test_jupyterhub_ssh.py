import re
import string
import time
import uuid

import paramiko
import pytest

from _nebari.utils import escape_string
from tests.tests_deployment import constants
from tests.tests_deployment.utils import monkeypatch_ssl_context

monkeypatch_ssl_context()

TIMEOUT_SECS = 300


@pytest.fixture(scope="session")
def paramiko_object(jupyterhub_access_token):
    """Connects to JupyterHub SSH cluster from outside the cluster.

    Ensures the JupyterLab pod is ready before attempting reauthentication
    by setting both `auth_timeout` and `banner_timeout` appropriately,
    and by retrying the connection until the pod is ready or a timeout occurs.
    """
    params = {
        "hostname": constants.NEBARI_HOSTNAME,
        "port": 8022,
        "username": constants.KEYCLOAK_USERNAME,
        "password": jupyterhub_access_token,
        "allow_agent": constants.PARAMIKO_SSH_ALLOW_AGENT,
        "look_for_keys": constants.PARAMIKO_SSH_LOOK_FOR_KEYS,
    }

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    yield ssh_client, params

    ssh_client.close()


def invoke_shell(
    client: paramiko.SSHClient, params: dict[str, any]
) -> paramiko.Channel:
    client.connect(**params)
    return client.invoke_shell()


def extract_output(delimiter: str, output: str) -> str:
    # Extract the command output between the start and end delimiters
    match = re.search(rf"{delimiter}start\n(.*)\n{delimiter}end", output, re.DOTALL)
    if match:
        print(match.group(1).strip())
        return match.group(1).strip()
    else:
        return output.strip()


def run_command_list(
    commands: list[str], channel: paramiko.Channel, wait_time: int = 0
) -> dict[str, str]:
    command_delimiters = {}
    for command in commands:
        delimiter = uuid.uuid4().hex
        command_delimiters[command] = delimiter
        b = channel.send(f"echo {delimiter}start; {command}; echo {delimiter}end\n")
        if b == 0:
            print(f"Command '{command}' failed to send")
    # Wait for the output to be ready before reading
    time.sleep(wait_time)
    while not channel.recv_ready():
        time.sleep(1)
        print("Waiting for output")
    output = ""
    while channel.recv_ready():
        output += channel.recv(65535).decode("utf-8")
    outputs = {}
    for command, delimiter in command_delimiters.items():
        command_output = extract_output(delimiter, output)
        outputs[command] = command_output
    return outputs


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_print_jupyterhub_ssh(paramiko_object):
    client, params = paramiko_object
    channel = invoke_shell(client, params)
    # Commands to run and just print the output
    commands_print = [
        "id",
        "env",
        "conda info",
        "df -h",
        "ls -la",
        "umask",
    ]
    outputs = run_command_list(commands_print, channel)
    for command, output in outputs.items():
        print(f"COMMAND: {command}")
        print(f"OUTPUT: {output}")
    channel.close()


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_exact_jupyterhub_ssh(paramiko_object):
    client, params = paramiko_object
    channel = invoke_shell(client, params)
    # Commands to run and exactly match output
    commands_exact = {
        "id -u": "1000",
        "id -g": "100",
        "whoami": constants.KEYCLOAK_USERNAME,
        "pwd": f"/home/{constants.KEYCLOAK_USERNAME}",
        "echo $HOME": f"/home/{constants.KEYCLOAK_USERNAME}",
        "conda activate default && echo $CONDA_PREFIX": "/opt/conda/envs/default",
        "hostname": f"jupyter-{escape_string(constants.KEYCLOAK_USERNAME, safe=set(string.ascii_lowercase + string.digits), escape_char='-').lower()}",
    }
    outputs = run_command_list(list(commands_exact.keys()), channel)
    for command, output in outputs.items():
        assert (
            output == outputs[command]
        ), f"Command '{command}' output '{outputs[command]}' does not match expected '{output}'"

    channel.close()


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_contains_jupyterhub_ssh(paramiko_object):
    client, params = paramiko_object
    channel = invoke_shell(client, params)

    # Commands to run and check if the output contains specific strings
    commands_contain = {
        "ls -la": ".bashrc",
        "cat ~/.bashrc": "Managed by Nebari",
        "cat ~/.profile": "Managed by Nebari",
        "cat ~/.bash_logout": "Managed by Nebari",
        # Ensure we don't copy over extra files from /etc/skel in init container
        "ls -la ~/..202*": "No such file or directory",
        "ls -la ~/..data": "No such file or directory",
    }

    outputs = run_command_list(commands_contain.keys(), channel, 30)
    for command, expected_output in commands_contain.items():
        assert (
            expected_output in outputs[command]
        ), f"Command '{command}' output does not contain expected substring '{expected_output}'. Instead got '{outputs[command]}'"

    channel.close()
