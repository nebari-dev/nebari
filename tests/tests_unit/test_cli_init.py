import os
import pytest
import tempfile
import yaml

from collections.abc import MutableMapping
from _nebari.cli import create_cli
from typer import Typer
from typer.testing import CliRunner

from typing import List

runner = CliRunner()

MOCK_ENV = [
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", # aws
    "GOOGLE_CREDENTIALS", "PROJECT_ID", # gcp
    "ARM_SUBSCRIPTION_ID", "ARM_TENANT_ID", "ARM_CLIENT_ID", "ARM_CLIENT_SECRET", # azure
    "DIGITALOCEAN_TOKEN", "SPACES_ACCESS_KEY_ID", "SPACES_SECRET_ACCESS_KEY", # digital ocean
    "GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "GITHUB_USERNAME", "GITHUB_TOKEN", # github
    "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET", "AUTH0_DOMAIN", # auth0
]

@pytest.mark.parametrize('args, exit_code, content', [
    # --help
    (['--help'], 0, ['init']),
    (['-h'], 0, ['init']),
    (['init', '--help'], 0, ['Create and initialize your nebari-config.yaml file']),
    (['init', '-h'], 0, ['Create and initialize your nebari-config.yaml file']),

    # error, missing args
    (['init'], 2, ['Missing option']),
    (['init', '--no-guided-init'], 2, ['Missing option']),
    (['init', '--project-name'], 2, ['requires an argument']),
    (['init', '--project'], 2, ['requires an argument']),
    (['init', '-p'], 2, ['requires an argument']),
    (['init', '--domain-name'], 2, ['requires an argument']),
    (['init', '--domain'], 2, ['requires an argument']),
    (['init', '--namespace'], 2, ['requires an argument']),
    (['init', '--auth-provider'], 2, ['requires an argument']),
    #(['init', '--auth-auto-provision'], 2, ['requires an argument']),
    #(['init', '--no-auth-auto-provision'], 2, ['requires an argument']),
    (['init', '--repository'], 2, ['requires an argument']),
    #(['init', '--repository-auto-provision'], 2, ['requires an argument']),
    #(['init', '--no-repository-auto-provision'], 2, ['requires an argument']),
    (['init', '--ci-provider'], 2, ['requires an argument']),
    (['init', '--terraform-state'], 2, ['requires an argument']),
    (['init', '--kubernetes-version'], 2, ['requires an argument']),
    (['init', '--ssl-cert-email'], 2, ['requires an argument']),
    # (['init', '--disable-prompt'], 2, ['requires an argument']),
    # (['init', '--no-disable-prompt'], 2, ['requires an argument']),
    (['init', '--output'], 2, ['requires an argument']),
    (['init', '-o'], 2, ['requires an argument']),
])
def test_init_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


# def test_init_guided_init():
#     app = create_cli()
#     result = runner.invoke(app, ['init', '--guided-init'], input = "\ntestprojectname\ntestprojectname.example.com\n\nN\ny\nnotreal@example.com\nn\n")
#     assert result.exit_code == 0

def test_all_init_no_guided_happy(monkeypatch, provider: str, project_name: str, domain_name: str, namespace: str, auth_provider: str, ci_provider: str, terraform_state: str, email: str):
    mock_cloud_provider_env(monkeypatch)

    app = create_cli()
    args = [
        "init", provider,
        "--project-name", project_name,
        "--domain-name", domain_name,
        "--namespace", namespace,
        "--auth-provider", auth_provider,
        "--ci-provider", ci_provider,
        "--terraform-state", terraform_state,
        "--ssl-cert-email", email,
    ]
    expected_yaml = f"""
    provider: {provider}
    namespace: {namespace}
    project_name: {project_name}
    domain: {domain_name}
    certificate:
        type: lets-encrypt
        acme_email: {email}
    ci_cd:
        type: {ci_provider}
    terraform_state:
        type: {terraform_state}
    security:
        authentication:
            type: {auth_provider}
    """

    assert_nebari_init_args(app, args, expected_yaml)


def assert_nebari_init_args(app: Typer, args: List[str], expected_yaml: str):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = os.path.join(tmp, 'nebari-config.yaml')
        print(f"\n>>>> Using tmp file {tmp_file}")
        assert os.path.exists(tmp_file) == False

        print(f"\n>>>> Testing nebari {args}")

        result = runner.invoke(app, args + ["--output", tmp_file, "--disable-prompt"])
        assert result.exit_code == 0
        assert os.path.exists(tmp_file) == True

        with open(tmp_file, 'r') as config_yaml:
            config = flatten_dict(yaml.safe_load(config_yaml))
            expected = flatten_dict(yaml.safe_load(expected_yaml))
            assert expected.items() <= config.items()


# https://stackoverflow.com/a/62186053
def flatten_dict(dictionary, parent_key=False, separator='.'):
    """
    Turn a nested dictionary into a flattened dictionary
    :param dictionary: The dictionary to flatten
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    """

    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten_dict({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)

###
# TODO:
# auth_provider - Auth0 and GitHub both prompt for credentials even when supplied by environment variable, custom throws an error that it doesn't exist
###
def pytest_generate_tests(metafunc):
    param_names = ["provider", "project_name", "domain_name", "namespace", "auth_provider", "ci_provider", "terraform_state", "email"]
    #if all(x in metafunc.fixturenames for x in param_names): # inject fixtures by matching argument names
    if metafunc.function.__name__.startswith("test_all_init_"): # inject by function naming convention
        test_data = []
        for provider in ["local", "aws", "azure", "gcp", "do", "existing"]: # ["local", "aws", "azure", "gcp", "do", "existing"]
            for project_name in ["testproject"]:
                for auth_provider in ["password"]: # ["password", "Auth0", "GitHub", "custom"]
                    for ci_provider in ["none", "github-actions", "gitlab-ci"]: # ["none", "github-actions", "gitlab-ci"]
                        for terraform_state in ["local", "remote", "existing"]:
                            test_data.append((provider, project_name, f"{project_name}.example.com", "test", auth_provider, ci_provider, terraform_state, "noreply@example.com"))

        metafunc.parametrize(",".join(param_names), test_data)
        
def mock_cloud_provider_env(monkeypatch):
    for e in MOCK_ENV:
        monkeypatch.setenv(e, "test")
