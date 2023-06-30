from nebari import schema
from nebari.plugins import nebari_plugin_manager


def test_minimal_schema():
    config = schema.Main(project_name="test")
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
