import re

import pytest

from qhub.provider import minikube
from qhub.constants import MINIKUBE_VERSION


def test_minikube_version():
    assert minikube.version() == MINIKUBE_VERSION


def test_minikube_start_status_delete():
    profile = "pytest-start-status-delete"

    try:
        minikube.start(profile=profile)
        assert minikube.status(profile=profile)
        assert re.fullmatch('\d+\.\d+\.\d+\.\d+', minikube.ip(profile=profile))
    finally:
        minikube.delete(profile=profile)
