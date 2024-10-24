import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import List

import pytest
import yaml
from typer import Typer
from typer.testing import CliRunner

from _nebari.cli import create_cli
from _nebari.constants import AZURE_DEFAULT_REGION

runner = CliRunner()

MOCK_KUBERNETES_VERSIONS = {
    "aws": ["1.20"],
    "azure": ["1.20"],
    "gcp": ["1.20"],
    "do": ["1.21.5-do.0"],
}
MOCK_CLOUD_REGIONS = {
    "aws": ["us-east-1"],
    "azure": [AZURE_DEFAULT_REGION],
    "gcp": ["us-central1"],
    "do": ["nyc3"],
}


@pytest.mark.parametrize(
    "args, exit_code, content",
    [
        # --help
        (["--help"], 0, ["Usage:", "nebari init"]),
        (["-h"], 0, ["Usage:", "nebari init"]),
        # error, missing args
        ([], 2, ["Missing option"]),
        (["--no-guided-init"], 2, ["Missing option"]),
        (["--project-name"], 2, ["requires an argument"]),
        (["--project"], 2, ["requires an argument"]),
        (["-p"], 2, ["requires an argument"]),
        (["--domain-name"], 2, ["requires an argument"]),
        (["--domain"], 2, ["requires an argument"]),
        (["--namespace"], 2, ["requires an argument"]),
        (["--auth-provider"], 2, ["requires an argument"]),
        (["--repository"], 2, ["requires an argument"]),
        (["--ci-provider"], 2, ["requires an argument"]),
        (["--terraform-state"], 2, ["requires an argument"]),
        (["--kubernetes-version"], 2, ["requires an argument"]),
        (["--region"], 2, ["requires an argument"]),
        (["--ssl-cert-email"], 2, ["requires an argument"]),
        (["--output"], 2, ["requires an argument"]),
        (["-o"], 2, ["requires an argument"]),
        (["--explicit"], 2, ["Missing option"]),
        (["-e"], 2, ["Missing option"]),
    ],
)
def test_cli_init_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["init"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


def generate_test_data_test_cli_init_happy_path():
    """
    Generate inputs to test_cli_init_happy_path representing all valid combinations of options
    available to nebari init
    """

    test_data = []
    for provider in ["local", "aws", "azure", "gcp", "do", "existing"]:
        for region in get_cloud_regions(provider):
            for project_name in ["testproject"]:
                for domain_name in [f"{project_name}.example.com"]:
                    for namespace in ["test-ns"]:
                        for auth_provider in ["password", "Auth0", "GitHub"]:
                            for ci_provider in [
                                "none",
                                "github-actions",
                                "gitlab-ci",
                            ]:
                                for terraform_state in [
                                    "local",
                                    "remote",
                                    "existing",
                                ]:
                                    for email in ["noreply@example.com"]:
                                        for (
                                            kubernetes_version
                                        ) in get_kubernetes_versions(provider) + [
                                            "latest"
                                        ]:
                                            for explicit in [True, False]:
                                                test_data.append(
                                                    (
                                                        provider,
                                                        region,
                                                        project_name,
                                                        domain_name,
                                                        namespace,
                                                        auth_provider,
                                                        ci_provider,
                                                        terraform_state,
                                                        email,
                                                        kubernetes_version,
                                                        explicit,
                                                    )
                                                )

    keys = [
        "provider",
        "region",
        "project_name",
        "domain_name",
        "namespace",
        "auth_provider",
        "ci_provider",
        "terraform_state",
        "email",
        "kubernetes_version",
        "explicit",
    ]
    return {"keys": keys, "test_data": test_data}


def test_cli_init_happy_path(
    provider: str,
    region: str,
    project_name: str,
    domain_name: str,
    namespace: str,
    auth_provider: str,
    ci_provider: str,
    terraform_state: str,
    email: str,
    kubernetes_version: str,
    explicit: bool,
):
    app = create_cli()
    args = [
        "init",
        provider,
        "--no-guided-init",  # default
        "--no-auth-auto-provision",  # default
        "--no-repository-auto-provision",  # default
        "--disable-prompt",
        "--project-name",
        project_name,
        "--domain-name",
        domain_name,
        "--namespace",
        namespace,
        "--auth-provider",
        auth_provider,
        "--ci-provider",
        ci_provider,
        "--terraform-state",
        terraform_state,
        "--ssl-cert-email",
        email,
        "--kubernetes-version",
        kubernetes_version,
        "--region",
        region,
    ]
    if explicit:
        args += ["--explicit"]

    expected_yaml = f"""
    provider: {provider}
    namespace: {namespace}
    project_name: {project_name}
    domain: {domain_name}
    ci_cd:
        type: {ci_provider}
    terraform_state:
        type: {terraform_state}
    security:
        authentication:
            type: {auth_provider}
    certificate:
        type: lets-encrypt
        acme_email: {email}
    """

    provider_section = get_provider_section_header(provider)
    if provider_section != "" and kubernetes_version != "latest":
        expected_yaml += f"""
    {provider_section}:
        kubernetes_version: '{kubernetes_version}'
        region: '{region}'
    """

    assert_nebari_init_args(app, args, expected_yaml)


def assert_nebari_init_args(
    app: Typer, args: List[str], expected_yaml: str, input: str = None
):
    """
    Run nebari init with happy path assertions and verify the generated yaml contains
    all values in expected_yaml.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        result = runner.invoke(
            app, args + ["--output", tmp_file.resolve()], input=input
        )

        assert not result.exception
        assert 0 == result.exit_code
        assert tmp_file.exists() is True

        with open(tmp_file.resolve(), "r") as config_yaml:
            config = flatten_dict(yaml.safe_load(config_yaml))
            expected = flatten_dict(yaml.safe_load(expected_yaml))
            assert expected.items() <= config.items()


def pytest_generate_tests(metafunc):
    """
    Dynamically generate test data parameters for test functions by looking for
    and executing an associated generate_test_data_{function_name} if one exists.
    """

    try:
        td = eval(f"generate_test_data_{metafunc.function.__name__}")()
        metafunc.parametrize(",".join(td["keys"]), td["test_data"])
    except Exception:
        # expected when a generate_test_data_ function doesn't exist
        pass


# https://stackoverflow.com/a/62186053
def flatten_dict(dictionary, parent_key=False, separator="."):
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


def get_provider_section_header(provider: str):
    if provider == "aws":
        return "amazon_web_services"
    if provider == "gcp":
        return "google_cloud_platform"
    if provider == "azure":
        return "azure"
    if provider == "do":
        return "digital_ocean"

    return ""


def get_cloud_regions(provider: str):
    if provider == "aws":
        return MOCK_CLOUD_REGIONS["aws"]
    if provider == "gcp":
        return MOCK_CLOUD_REGIONS["gcp"]
    if provider == "azure":
        return MOCK_CLOUD_REGIONS["azure"]
    if provider == "do":
        return MOCK_CLOUD_REGIONS["do"]

    return ""


def get_kubernetes_versions(provider: str):
    if provider == "aws":
        return MOCK_KUBERNETES_VERSIONS["aws"]
    if provider == "gcp":
        return MOCK_KUBERNETES_VERSIONS["gcp"]
    if provider == "azure":
        return MOCK_KUBERNETES_VERSIONS["azure"]
    if provider == "do":
        return MOCK_KUBERNETES_VERSIONS["do"]

    return ""
