import nebari.schema


def test_minimal_schema():
    config = nebari.schema.Main(project_name="test")
    assert config.project_name == "test"
    assert config.storage.conda_store == "200Gi"


def test_minimal_schema_from_file(tmp_path):
    filename = tmp_path / "nebari-config.yaml"
    with filename.open("w") as f:
        f.write("project_name: test\n")

    config = nebari.schema.read_configuration(filename)
    assert config.project_name == "test"
    assert config.storage.conda_store == "200Gi"


def test_minimal_schema_from_file_with_env(tmp_path, monkeypatch):
    filename = tmp_path / "nebari-config.yaml"
    with filename.open("w") as f:
        f.write("project_name: test\n")

    monkeypatch.setenv("NEBARI_SECRET__project_name", "env")
    monkeypatch.setenv("NEBARI_SECRET__storage__conda_store", "1000Gi")

    config = nebari.schema.read_configuration(filename)
    assert config.project_name == "env"
    assert config.storage.conda_store == "1000Gi"


def test_minimal_schema_from_file_with_env(tmp_path, monkeypatch):
    filename = tmp_path / "nebari-config.yaml"
    with filename.open("w") as f:
        f.write("project_name: test\n")

    monkeypatch.setenv("NEBARI_SECRET__project_name", "env")
    monkeypatch.setenv("NEBARI_SECRET__storage__conda_store", "1000Gi")

    config = nebari.schema.read_configuration(filename, read_environment=False)
    assert config.project_name == "test"
    assert config.storage.conda_store == "200Gi"


def test_render_schema(setup_fixture, render_config_partial):
    (nebari_config_loc, render_config_inputs) = setup_fixture
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = render_config_inputs

    config = render_config_partial(
        project_name=project,
        namespace=namespace,
        nebari_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        auth_provider=auth_provider,
        kubernetes_version=None,
    )
    assert config.project_name == project
    assert config.namespace == namespace
