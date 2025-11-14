from contextlib import nullcontext
from pathlib import Path

import pytest
from rich.prompt import Confirm, Prompt

from _nebari.upgrade import do_upgrade
from _nebari.version import __version__, rounded_ver_parse
from nebari.plugins import nebari_plugin_manager


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


class MockKeycloakAdmin:
    @staticmethod
    def get_client_id(*args, **kwargs):
        return "test-client"

    @staticmethod
    def create_client_role(*args, **kwargs):
        return "test-client-role"

    @staticmethod
    def get_client_role_id(*args, **kwargs):
        return "test-client-role-id"

    @staticmethod
    def get_role_by_id(*args, **kwargs):
        return bytearray("test-role-id", "utf-8")

    @staticmethod
    def get_groups(*args, **kwargs):
        return []

    @staticmethod
    def get_client_role_groups(*args, **kwargs):
        return []

    @staticmethod
    def assign_group_client_roles(*args, **kwargs):
        pass


@pytest.mark.parametrize(
    "old_qhub_config_path_str,attempt_fixes,expect_upgrade_error",
    [
        (
            "./qhub-config-yaml-files-for-upgrade/qhub-config-aws-310.yaml",
            False,
            False,
        ),
        (
            "./qhub-config-yaml-files-for-upgrade/qhub-config-aws-310-customauth.yaml",
            False,
            True,
        ),
        (
            "./qhub-config-yaml-files-for-upgrade/qhub-config-aws-310-customauth.yaml",
            True,
            False,
        ),
    ],
)
def test_upgrade_4_0(
    old_qhub_config_path_str,
    attempt_fixes,
    expect_upgrade_error,
    tmp_path,
    qhub_users_import_json,
    monkeypatch,
):
    def mock_input(prompt, **kwargs):
        from _nebari.upgrade import TERRAFORM_REMOVE_TERRAFORM_STAGE_FILES_CONFIRMATION

        # Mock different upgrade steps prompt answers
        if prompt == "Have you deleted the Argo Workflows CRDs and service accounts?":
            return True
        elif (
            prompt
            == "\nDo you want Nebari to update the kube-prometheus-stack CRDs and delete the prometheus-node-exporter for you? If not, you'll have to do it manually."
        ):
            return False
        elif (
            prompt
            == "Have you backed up your custom dashboards (if necessary), deleted the prometheus-node-exporter daemonset and updated the kube-prometheus-stack CRDs?"
        ):
            return True
        elif (
            prompt
            == "[bold]Would you like Nebari to assign the corresponding role/scopes to all of your current groups automatically?[/bold]"
        ):
            return False
        elif prompt == TERRAFORM_REMOVE_TERRAFORM_STAGE_FILES_CONFIRMATION:
            return attempt_fixes
        elif (
            prompt
            == "\nWould you like Nebari to backup the Keycloak database for you now?"
        ):
            # Always backup in tests so upgrade can complete
            return True
        # All other prompts will be answered with "y"
        else:
            return True

    def mock_prompt_ask(prompt, **kwargs):
        # Mock context selection for 2025.11.1 upgrade
        if "Select context number" in prompt:
            return "1"  # Select first context
        return ""

    monkeypatch.setattr(Confirm, "ask", mock_input)
    monkeypatch.setattr(Prompt, "ask", mock_prompt_ask)

    from kubernetes import config as _kube_config
    from kubernetes.client import ApiextensionsV1Api as _ApiextensionsV1Api
    from kubernetes.client import AppsV1Api as _AppsV1Api
    from kubernetes.client import CoreV1Api as _CoreV1Api
    from kubernetes.client import V1Status as _V1Status

    def monkey_patch_delete_crd(*args, **kwargs):
        return _V1Status(code=200)

    def monkey_patch_delete_namespaced_sa(*args, **kwargs):
        return _V1Status(code=200)

    def monkey_patch_list_namespaced_daemon_set(*args, **kwargs):
        class MonkeypatchApiResponse:
            items = False

        return MonkeypatchApiResponse

    def monkey_patch_read_namespaced_pod(*args, **kwargs):
        # Mock the pod exists for keycloak backup
        class MockPod:
            metadata = type("obj", (object,), {"name": "keycloak-postgresql-0"})

        return MockPod()

    monkeypatch.setattr(
        _kube_config,
        "load_kube_config",
        lambda *args, **kwargs: None,
    )
    # Mock kubectl contexts for 2025.11.1 upgrade
    mock_contexts = [
        {"name": "test-context", "context": {"cluster": "test-cluster"}},
    ]
    mock_active_context = mock_contexts[0]
    monkeypatch.setattr(
        _kube_config,
        "list_kube_config_contexts",
        lambda *args, **kwargs: (mock_contexts, mock_active_context),
    )
    monkeypatch.setattr(
        _ApiextensionsV1Api,
        "delete_custom_resource_definition",
        monkey_patch_delete_crd,
    )
    monkeypatch.setattr(
        _CoreV1Api,
        "delete_namespaced_service_account",
        monkey_patch_delete_namespaced_sa,
    )
    monkeypatch.setattr(
        _ApiextensionsV1Api,
        "read_custom_resource_definition",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        _ApiextensionsV1Api,
        "patch_custom_resource_definition",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        _AppsV1Api,
        "list_namespaced_daemon_set",
        monkey_patch_list_namespaced_daemon_set,
    )
    monkeypatch.setattr(
        _CoreV1Api,
        "read_namespaced_pod",
        monkey_patch_read_namespaced_pod,
    )

    # Mock connect_get_namespaced_pod_exec to prevent real API calls
    def monkey_patch_connect_pod_exec(*args, **kwargs):
        # This should not be called if stream mock works, but add as safety
        class MockExecResponse:
            def read_stdout(self):
                return "-- PostgreSQL database dump\n"

            def read_stderr(self):
                return ""

        return MockExecResponse()

    monkeypatch.setattr(
        _CoreV1Api,
        "connect_get_namespaced_pod_exec",
        monkey_patch_connect_pod_exec,
    )

    # Mock kubernetes stream for database backup
    class MockStreamResponse:
        def __init__(self):
            self._open = True
            self._stdout_data = "-- PostgreSQL database dump\n-- Dump completed\n"
            self._read_count = 0

        def is_open(self):
            # Close after reading data
            return self._read_count < 1

        def peek_stdout(self):
            return self._read_count < 1

        def read_stdout(self):
            self._read_count += 1
            return self._stdout_data

        def peek_stderr(self):
            return False

        def read_stderr(self):
            return ""

        def update(self, timeout=1):
            pass

        def close(self):
            self._open = False

    def mock_stream(*args, **kwargs):
        return MockStreamResponse()

    # Patch stream in the upgrade module where it's imported
    from _nebari import upgrade as _upgrade

    monkeypatch.setattr(_upgrade, "stream", mock_stream)

    def monkey_patch_get_keycloak_admin(*args, **kwargs):
        return MockKeycloakAdmin()

    monkeypatch.setattr(
        _upgrade,
        "get_keycloak_admin",
        monkey_patch_get_keycloak_admin,
    )

    # In 2025.4.1, upgrade unit tests are failing in the following line of the upgrade logic:
    # https://github.com/nebari-dev/nebari/blob/6bf35baf8d6c8650ffa6839445cd7c70b0ee5ada/src/_nebari/upgrade.py#L1781
    # This is because when installing Nebari from source, the version is different from
    # 2025.4.1, resulting in a Pydantic validation error. Thus, we mock the check_default
    # validator to skip it during the upgrade tests.
    # Note that this error is not present when installing Nebari from the release version,
    # so fixing it here seems appropriate.
    from nebari.schema import Main

    monkeypatch.setattr(Main, "check_default", lambda _: None)

    old_qhub_config_path = Path(__file__).parent / old_qhub_config_path_str

    tmp_qhub_config = Path(tmp_path, old_qhub_config_path.name)
    tmp_qhub_config.write_text(old_qhub_config_path.read_text())  # Copy contents to tmp

    orig_contents = tmp_qhub_config.read_text()  # Read in initial contents

    assert not Path(tmp_path, "qhub-users-import.json").exists()

    # Do the upgrade
    if not expect_upgrade_error:
        do_upgrade(
            tmp_qhub_config, attempt_fixes
        )  # Would raise an error if invalid by current Nebari version's standards
    else:
        with pytest.raises(ValueError):
            do_upgrade(tmp_qhub_config, attempt_fixes)
        return

    # Check the resulting YAML
    config = nebari_plugin_manager.read_config(tmp_qhub_config)

    assert len(config.security.keycloak.initial_root_password) == 16
    assert not hasattr(config.security, "users")
    assert not hasattr(config.security, "groups")

    __rounded_version__ = rounded_ver_parse(__version__)

    # Check image versions have been bumped up
    assert (
        config.default_images.jupyterhub
        == f"quansight/nebari-jupyterhub:v{__rounded_version__}"
    )
    assert (
        config.profiles.jupyterlab[0].kubespawner_override.image
        == f"quansight/nebari-jupyterlab:v{__rounded_version__}"
    )
    assert config.security.authentication.type != "custom"

    # Keycloak import users json
    assert (
        Path(tmp_path, "nebari-users-import.json").read_text().rstrip()
        == qhub_users_import_json
    )

    # Check backup
    tmp_qhub_config_backup = Path(tmp_path, f"{old_qhub_config_path.name}.old.backup")

    assert orig_contents == tmp_qhub_config_backup.read_text()

    # Check Keycloak database backup file was created (from 2025.11.1 upgrade)
    keycloak_backup_file = Path(tmp_path, "keycloak-backup.sql")
    assert keycloak_backup_file.exists()
    # Verify backup contains postgres dump content
    backup_content = keycloak_backup_file.read_text()
    assert "PostgreSQL database dump" in backup_content


@pytest.mark.parametrize(
    "version_str, exception",
    [
        ("1.0.0", nullcontext()),
        ("1.cool.0", pytest.raises(ValueError, match=r"Invalid version string .*")),
        ("0,1.0", pytest.raises(ValueError, match=r"Invalid version string .*")),
        ("", pytest.raises(ValueError, match=r"Invalid version string .*")),
        (
            "1.0.0-rc1",
            pytest.raises(
                AssertionError,
                match=r"Invalid version .*: must be a full release version, not a dev/prerelease/postrelease version",
            ),
        ),
        (
            "1.0.0dev1",
            pytest.raises(
                AssertionError,
                match=r"Invalid version .*: must be a full release version, not a dev/prerelease/postrelease version",
            ),
        ),
    ],
)
def test_version_string(new_upgrade_cls, version_str, exception):
    with exception:

        class DummyUpgrade(new_upgrade_cls):
            version = version_str


def test_duplicated_version(new_upgrade_cls):
    duplicated_version = "1.2.3"
    with pytest.raises(
        AssertionError, match=rf"Duplicate UpgradeStep version {duplicated_version}"
    ):

        class DummyUpgrade(new_upgrade_cls):
            version = duplicated_version

        class DummyUpgrade2(new_upgrade_cls):
            version = duplicated_version

        class DummyUpgrade3(new_upgrade_cls):
            version = "1.2.4"
