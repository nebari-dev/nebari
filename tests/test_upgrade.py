import pytest
from pathlib import Path
from pydantic.error_wrappers import ValidationError

from qhub.upgrade import do_upgrade, __version__, load_yaml, verify


@pytest.fixture
def qhub_users_import_json():
    return (
        (
            Path(__file__).parent
            / "./qhub-config-yaml-files-for-upgrade/qhub-users-import.json"
        )
        .read_text()
        .rstrip()
    )


@pytest.mark.parametrize(
    "old_qhub_config_path_str,expect_verify_error",
    [
        ("./qhub-config-yaml-files-for-upgrade/qhub-config-do-310.yaml", False),
        (
            "./qhub-config-yaml-files-for-upgrade/qhub-config-do-310-customauth.yaml",
            True,
        ),
    ],
)
def test_upgrade(
    old_qhub_config_path_str, expect_verify_error, tmp_path, qhub_users_import_json
):
    old_qhub_config_path = Path(__file__).parent / old_qhub_config_path_str

    tmp_qhub_config = Path(tmp_path, old_qhub_config_path.name)
    tmp_qhub_config.write_text(old_qhub_config_path.read_text())  # Copy contents to tmp

    orig_contents = tmp_qhub_config.read_text()  # Read in initial contents

    assert not Path(tmp_path, "qhub-users-import.json").exists()

    # Do the updgrade
    do_upgrade(tmp_qhub_config)

    # Check the resulting YAML
    config = load_yaml(tmp_qhub_config)

    if not expect_verify_error:
        verify(
            config
        )  # Would raise an error if invalid by current QHub version's standards
    else:
        with pytest.raises(ValidationError):
            verify(config)

    assert len(config["security"]["keycloak"]["initial_root_password"]) == 16

    assert "users" not in config["security"]
    assert "groups" not in config["security"]

    # Check image versions have been bumped up
    assert (
        config["default_images"]["jupyterhub"]
        == f"quansight/qhub-jupyterhub:v{__version__}"
    )
    assert (
        config["profiles"]["jupyterlab"][0]["kubespawner_override"]["image"]
        == f"quansight/qhub-jupyterlab:v{__version__}"
    )

    # Keycloak import users json
    assert (
        Path(tmp_path, "qhub-users-import.json").read_text().rstrip()
        == qhub_users_import_json
    )

    # Check backup
    tmp_qhub_config_backup = Path(tmp_path, f"{old_qhub_config_path.name}.old.backup")

    assert orig_contents == tmp_qhub_config_backup.read_text()
