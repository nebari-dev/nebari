import pytest

from qhub.provider import minikube
from qhub.constants import MINIKUBE_VERSION


def test_minikube_version():
    assert minikube.version() == MINIKUBE_VERSION


def test_minikube_start_status_delete():
    profile = "pytest-test_minikube_start_status_delete"

    try:
        minikube.start(profile=profile)
    finally:
        minikube.delete(profile=profile)
