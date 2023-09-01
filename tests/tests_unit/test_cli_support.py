import tempfile
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch
from zipfile import ZipFile

import kubernetes.client
import kubernetes.client.exceptions
import pytest
import yaml
from typer.testing import CliRunner

from _nebari.cli import create_cli

runner = CliRunner()


class MockPod:
    name: str
    containers: List[str]
    ip_address: str

    def __init__(self, name: str, ip_address: str, containers: List[str]):
        self.name = name
        self.ip_address = ip_address
        self.containers = containers


def mock_list_namespaced_pod(pods: List[MockPod], namespace: str):
    return kubernetes.client.V1PodList(
        items=[
            kubernetes.client.V1Pod(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=p.name, namespace=namespace
                ),
                spec=kubernetes.client.V1PodSpec(
                    containers=[
                        kubernetes.client.V1Container(name=c) for c in p.containers
                    ]
                ),
                status=kubernetes.client.V1PodStatus(pod_ip=p.ip_address),
            )
            for p in pods
        ]
    )


def mock_read_namespaced_pod_log(name: str, namespace: str, container: str):
    return f"Test log entry: {name} -- {namespace} -- {container}"


@pytest.mark.parametrize(
    "args, exit_code, content",
    [
        # --help
        (["--help"], 0, ["Usage:"]),
        (["-h"], 0, ["Usage:"]),
        # error, missing args
        ([], 2, ["Missing option"]),
        (["--config"], 2, ["requires an argument"]),
        (["-c"], 2, ["requires an argument"]),
        (["--output"], 2, ["requires an argument"]),
        (["-o"], 2, ["requires an argument"]),
    ],
)
def test_cli_support_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["support"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


@patch("kubernetes.config.kube_config.load_kube_config", return_value=Mock())
@patch(
    "kubernetes.client.CoreV1Api",
    return_value=Mock(
        list_namespaced_pod=Mock(
            side_effect=lambda namespace: mock_list_namespaced_pod(
                [
                    MockPod(
                        name="pod-1",
                        ip_address="10.0.0.1",
                        containers=["container-1-1", "container-1-2"],
                    ),
                    MockPod(
                        name="pod-2",
                        ip_address="10.0.0.2",
                        containers=["container-2-1"],
                    ),
                ],
                namespace,
            )
        ),
        read_namespaced_pod_log=Mock(side_effect=mock_read_namespaced_pod_log),
    ),
)
def test_cli_support_happy_path(
    _mock_k8s_corev1api, _mock_config, monkeypatch: pytest.MonkeyPatch
):
    with tempfile.TemporaryDirectory() as tmp:
        # NOTE: The support command leaves the ./log folder behind after running,
        # relative to wherever the tests were run from.
        # Changing context to the tmp dir so this will be cleaned up properly.
        monkeypatch.chdir(Path(tmp).resolve())

        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        with open(tmp_file.resolve(), "w") as f:
            yaml.dump({"project_name": "support", "namespace": "test-ns"}, f)

        assert tmp_file.exists() is True

        app = create_cli()

        log_zip_file = Path(tmp).resolve() / "test-support.zip"
        assert log_zip_file.exists() is False

        result = runner.invoke(
            app,
            [
                "support",
                "--config",
                tmp_file.resolve(),
                "--output",
                log_zip_file.resolve(),
            ],
        )

        assert log_zip_file.exists() is True

        assert 0 == result.exit_code
        assert not result.exception
        assert "log/test-ns" in result.stdout

        # open the zip and check a sample file for the expected formatting
        with ZipFile(log_zip_file.resolve(), "r") as log_zip:
            # expect 1 log file per pod
            assert 2 == len(log_zip.namelist())
            with log_zip.open("log/test-ns/pod-1.txt") as log_file:
                content = str(log_file.read(), "UTF-8")
                # expect formatted header + logs for each container
                expected = """
10.0.0.1\ttest-ns\tpod-1
Container: container-1-1
Test log entry: pod-1 -- test-ns -- container-1-1
Container: container-1-2
Test log entry: pod-1 -- test-ns -- container-1-2
"""
                assert expected.strip() == content.strip()


@patch("kubernetes.config.kube_config.load_kube_config", return_value=Mock())
@patch(
    "kubernetes.client.CoreV1Api",
    return_value=Mock(
        list_namespaced_pod=Mock(
            side_effect=kubernetes.client.exceptions.ApiException(reason="unit testing")
        )
    ),
)
def test_cli_support_error_apiexception(
    _mock_k8s_corev1api, _mock_config, monkeypatch: pytest.MonkeyPatch
):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.chdir(Path(tmp).resolve())

        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        with open(tmp_file.resolve(), "w") as f:
            yaml.dump({"project_name": "support", "namespace": "test-ns"}, f)

        assert tmp_file.exists() is True

        app = create_cli()

        log_zip_file = Path(tmp).resolve() / "test-support.zip"

        result = runner.invoke(
            app,
            [
                "support",
                "--config",
                tmp_file.resolve(),
                "--output",
                log_zip_file.resolve(),
            ],
        )

        assert log_zip_file.exists() is False

        assert 1 == result.exit_code
        assert result.exception
        assert "Reason: unit testing" in str(result.exception)


def test_cli_support_error_missing_config():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        app = create_cli()

        result = runner.invoke(app, ["support", "--config", tmp_file.resolve()])

        assert 1 == result.exit_code
        assert result.exception
        assert "nebari-config.yaml does not exist" in str(result.exception)
