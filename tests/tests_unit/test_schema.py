from contextlib import nullcontext

import pytest
from pydantic import ValidationError

from nebari import schema
from nebari.plugins import nebari_plugin_manager


def test_minimal_schema():
    config = nebari_plugin_manager.config_schema(project_name="test")
    assert config.project_name == "test"
    assert config.storage.conda_store == "200Gi"


def test_minimal_schema_from_file(tmp_path):
    filename = tmp_path / "nebari-config.yaml"
    with filename.open("w") as f:
        f.write("project_name: test\n")

    config = nebari_plugin_manager.read_config(filename)
    assert config.project_name == "test"
    assert config.storage.conda_store == "200Gi"


def test_minimal_schema_from_file_with_env(tmp_path, monkeypatch):
    filename = tmp_path / "nebari-config.yaml"
    with filename.open("w") as f:
        f.write("project_name: test\n")

    monkeypatch.setenv("NEBARI_SECRET__project_name", "env")
    monkeypatch.setenv("NEBARI_SECRET__storage__conda_store", "1000Gi")

    config = nebari_plugin_manager.read_config(filename)
    assert config.project_name == "env"
    assert config.storage.conda_store == "1000Gi"


def test_minimal_schema_from_file_without_env(tmp_path, monkeypatch):
    filename = tmp_path / "nebari-config.yaml"
    with filename.open("w") as f:
        f.write("project_name: test\n")

    monkeypatch.setenv("NEBARI_SECRET__project_name", "env")
    monkeypatch.setenv("NEBARI_SECRET__storage__conda_store", "1000Gi")

    config = nebari_plugin_manager.read_config(filename, read_environment=False)
    assert config.project_name == "test"
    assert config.storage.conda_store == "200Gi"


@pytest.mark.parametrize(
    "provider, exception",
    [
        (
            "fake",
            pytest.raises(
                ValueError,
                match="'fake' is not a valid enumeration member; permitted: local, existing, do, aws, gcp, azure",
            ),
        ),
        ("aws", nullcontext()),
        ("gcp", nullcontext()),
        ("do", nullcontext()),
        ("azure", nullcontext()),
        ("existing", nullcontext()),
        ("local", nullcontext()),
    ],
)
def test_provider_validation(config_schema, provider, exception):
    config_dict = {
        "project_name": "test",
        "provider": f"{provider}",
    }
    with exception:
        config = config_schema(**config_dict)
        assert config.provider == provider


@pytest.mark.parametrize(
    "provider, full_name, default_fields",
    [
        ("local", "local", {}),
        ("existing", "existing", {}),
        (
            "aws",
            "amazon_web_services",
            {"region": "us-east-1", "kubernetes_version": "1.18"},
        ),
        (
            "gcp",
            "google_cloud_platform",
            {
                "region": "us-east1",
                "project": "test-project",
                "kubernetes_version": "1.18",
            },
        ),
        (
            "do",
            "digital_ocean",
            {"region": "nyc3", "kubernetes_version": "1.19.2-do.3"},
        ),
        (
            "azure",
            "azure",
            {
                "region": "eastus",
                "kubernetes_version": "1.18",
                "storage_account_postfix": "test",
            },
        ),
    ],
)
def test_no_provider(config_schema, provider, full_name, default_fields):
    config_dict = {
        "project_name": "test",
        f"{full_name}": default_fields,
    }
    config = config_schema(**config_dict)
    assert config.provider == provider
    assert full_name in config.model_dump()


def test_multiple_providers(config_schema):
    config_dict = {
        "project_name": "test",
        "local": {},
        "existing": {},
    }
    msg = r"Multiple providers set: \['local', 'existing'\]"
    with pytest.raises(ValidationError, match=msg):
        config_schema(**config_dict)


def test_aws_premissions_boundary(config_schema):
    permissions_boundary = "arn:aws:iam::123456789012:policy/MyBoundaryPolicy"
    config_dict = {
        "project_name": "test",
        "provider": "aws",
        "amazon_web_services": {
            "region": "us-east-1",
            "kubernetes_version": "1.19",
            "permissions_boundary": f"{permissions_boundary}",
        },
    }
    config = config_schema(**config_dict)
    assert config.provider == "aws"
    assert config.amazon_web_services.permissions_boundary == permissions_boundary


@pytest.mark.parametrize("provider", ["local", "existing"])
def test_setted_provider(config_schema, provider):
    config_dict = {
        "project_name": "test",
        "provider": provider,
        f"{provider}": {"kube_context": "some_context"},
    }
    config = config_schema(**config_dict)
    assert config.provider == provider
    result_config_dict = config.model_dump()
    assert provider in result_config_dict
    assert result_config_dict[provider]["kube_context"] == "some_context"


def test_invalid_nebari_version(config_schema):
    nebari_version = "9999.99.9"
    config_dict = {
        "project_name": "test",
        "provider": "local",
        "nebari_version": f"{nebari_version}",
    }
    with pytest.raises(
        ValidationError,
        match=rf".* Assertion failed, nebari_version={nebari_version} is not an accepted version.*",
    ):
        config_schema(**config_dict)


def test_unsupported_kubernetes_version(config_schema):
    # the mocked available kubernetes versions are 1.18, 1.19, 1.20
    unsupported_version = "1.23"
    config_dict = {
        "project_name": "test",
        "provider": "gcp",
        "google_cloud_platform": {
            "project": "test",
            "region": "us-east1",
            "kubernetes_version": f"{unsupported_version}",
        },
    }
    with pytest.raises(
        ValidationError,
        match=rf"Invalid `kubernetes-version` provided: {unsupported_version}..*",
    ):
        config_schema(**config_dict)


@pytest.mark.parametrize(
    "auth_provider, env_vars",
    [
        (
            "Auth0",
            [
                "AUTH0_CLIENT_ID",
                "AUTH0_CLIENT_SECRET",
                "AUTH0_DOMAIN",
            ],
        ),
        (
            "GitHub",
            [
                "GITHUB_CLIENT_ID",
                "GITHUB_CLIENT_SECRET",
            ],
        ),
    ],
)
def test_missing_auth_env_var(monkeypatch, config_schema, auth_provider, env_vars):
    # auth related variables are all globally mocked, reset here
    monkeypatch.undo()
    for env_var in env_vars:
        monkeypatch.delenv(env_var, raising=False)

    config_dict = {
        "provider": "local",
        "project_name": "test",
        "security": {"authentication": {"type": auth_provider}},
    }
    with pytest.raises(
        ValidationError,
        match=r".* is not set in the environment",
    ):
        config_schema(**config_dict)


@pytest.mark.parametrize(
    "provider, addl_config, env_vars",
    [
        (
            "aws",
            {
                "amazon_web_services": {
                    "kubernetes_version": "1.20",
                    "region": "us-east-1",
                }
            },
            ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        ),
        (
            "azure",
            {
                "azure": {
                    "kubernetes_version": "1.20",
                    "region": "Central US",
                    "storage_account_postfix": "test",
                }
            },
            [
                "ARM_SUBSCRIPTION_ID",
                "ARM_TENANT_ID",
                "ARM_CLIENT_ID",
                "ARM_CLIENT_SECRET",
            ],
        ),
        (
            "gcp",
            {
                "google_cloud_platform": {
                    "kubernetes_version": "1.20",
                    "region": "us-east1",
                    "project": "test",
                }
            },
            ["GOOGLE_CREDENTIALS", "PROJECT_ID"],
        ),
        (
            "do",
            {"digital_ocean": {"kubernetes_version": "1.20", "region": "nyc3"}},
            ["DIGITALOCEAN_TOKEN", "SPACES_ACCESS_KEY_ID", "SPACES_SECRET_ACCESS_KEY"],
        ),
    ],
)
def test_missing_cloud_env_var(
    monkeypatch, config_schema, provider, addl_config, env_vars
):
    # cloud methods are all globally mocked, need to reset so the env variables will be checked
    monkeypatch.undo()
    for env_var in env_vars:
        monkeypatch.delenv(env_var, raising=False)

    nebari_config = {
        "provider": provider,
        "project_name": "test",
    }
    nebari_config.update(addl_config)

    with pytest.raises(
        ValidationError,
        match=r".* Missing the following required environment variables: .*",
    ):
        config_schema(**nebari_config)
