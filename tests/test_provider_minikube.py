import pytest

from qhub.provider import minikube
from qhub.contstants import MINIKUBE_VERSION


def test_minikube_version():
    assert minikube.version() == MINIKUBE_VERSION
