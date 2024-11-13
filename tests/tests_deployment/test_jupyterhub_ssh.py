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
        "auth_timeout": TIMEOUT_SECS,
        "banner_timeout": TIMEOUT_SECS,
    }

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    max_attempts = int(TIMEOUT_SECS / 10)
    delay = 10  # seconds

    for attempt in range(max_attempts):
        try:
            ssh_client.connect(**params)
            break
        except (
            paramiko.ssh_exception.NoValidConnectionsError,
            paramiko.ssh_exception.SSHException,
        ):
            print(
                f"SSH connection failed on attempt {attempt + 1}/{max_attempts}, "
                f"retrying in {delay} seconds..."
            )
            time.sleep(delay)
    else:
        pytest.fail("Could not establish SSH connection after multiple attempts.")

    yield ssh_client

    ssh_client.close()


def run_command(command, channel):
    delimiter = uuid.uuid4().hex
    channel.send(f"echo {delimiter}start; {command}; echo {delimiter}end\n")

    output = ""

    while True:
        if channel.recv_ready():
            recv = channel.recv(1024).decode("utf-8")
            output += recv
            if f"{delimiter}end" in recv:
                break
        else:
            time.sleep(0.1)  # Slight delay to prevent busy-waiting

    # Extract the command output between the start and end delimiters
    match = re.search(f"{delimiter}start(.*){delimiter}end", output, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return output.strip()


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_simple_jupyterhub_ssh(paramiko_object):
    channel = paramiko_object.invoke_shell()
    channel.close()


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_print_jupyterhub_ssh(paramiko_object):
    channel = paramiko_object.invoke_shell()

    # Commands to run and just print the output
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
        print(run_command(command, channel))

    channel.close()


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_exact_jupyterhub_ssh(paramiko_object):
    channel = paramiko_object.invoke_shell()

    # Commands to run and exactly match output
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

    for command, expected_output in commands_exact:
        output = run_command(command, channel)
        assert (
            output == expected_output
        ), f"Command '{command}' output '{output}' does not match expected '{expected_output}'"

    channel.close()


@pytest.mark.timeout(TIMEOUT_SECS)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_contains_jupyterhub_ssh(paramiko_object):
    channel = paramiko_object.invoke_shell()

    # Commands to run and check if the output contains specific strings
    commands_contain = [
        ("ls -la", ".bashrc"),
        ("cat ~/.bashrc", "Managed by Nebari"),
        ("cat ~/.profile", "Managed by Nebari"),
        ("cat ~/.bash_logout", "Managed by Nebari"),
        # Ensure we don't copy over extra files from /etc/skel in init container
        ("ls -la ~/..202*", "No such file or directory"),
        ("ls -la ~/..data", "No such file or directory"),
    ]

    for command, expected_substring in commands_contain:
        output = run_command(command, channel)
        assert (
            expected_substring in output
        ), f"Command '{command}' output does not contain expected substring '{expected_substring}'"

    channel.close()
