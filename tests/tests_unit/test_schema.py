from contextlib import nullcontext

import pytest
from pydantic import ValidationError

from _nebari.stages.infrastructure import (
    DEFAULT_GENERAL_NODE_GROUP_TAINTS,
    DEFAULT_NODE_GROUP_TAINTS,
)
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


def test_render_schema(nebari_config):
    assert isinstance(nebari_config, schema.Main)
    assert nebari_config.project_name == f"pytest{nebari_config.provider.value}"
    assert nebari_config.namespace == "dev"


@pytest.mark.parametrize(
    "provider, exception",
    [
        (
            "fake",
            pytest.raises(
                ValueError,
                match="'fake' is not a valid enumeration member; permitted: local, existing, aws, gcp, azure",
            ),
        ),
        ("aws", nullcontext()),
        ("gcp", nullcontext()),
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
def test_node_group_default_taints_set(
    config_schema, provider, full_name, default_fields
):
    config_dict = {
        "project_name": "test",
        "provider": f"{provider}",
        f"{full_name}": default_fields,
    }
    config = config_schema(**config_dict)
    ng = getattr(config, schema.provider_enum_name_map[config.provider]).node_groups
    for ng_name in ng:
        if ng_name == "general":
            assert ng[ng_name].taints == DEFAULT_GENERAL_NODE_GROUP_TAINTS
        else:
            assert ng[ng_name].taints == DEFAULT_NODE_GROUP_TAINTS


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


def test_aws_permissions_boundary(config_schema):
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
def test_set_provider(config_schema, provider):
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


def test_provider_config_mismatch_warning(config_schema):
    config_dict = {
        "project_name": "test",
        "provider": "local",
        "existing": {"kube_context": "some_context"},  # <-- Doesn't match the provider
    }
    with pytest.warns(UserWarning, match="configuration defined for other providers"):
        config_schema(**config_dict)
