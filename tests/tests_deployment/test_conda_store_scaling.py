import base64
import json
import logging
import os
import sys
import time
import uuid

import kubernetes.client
import pytest
import requests
from kubernetes import config, dynamic

from tests.tests_deployment import constants

CONDA_STORE_API_ENDPOINT = "conda-store/api/v1"
NEBARI_HOSTNAME = constants.NEBARI_HOSTNAME
NAMESPACE = os.getenv("CONDA_STORE_SERVICE_NAMESPACE")
# NEBARI_HOSTNAME = "local.quansight.dev" ## Override for local testing
TEST_CONDASTORE_WOKER_COUNT = os.getenv("TEST_CONDASTORE_WOKER_COUNT", 1)
count = TEST_CONDASTORE_WOKER_COUNT

from base64 import b64encode

log = logging.getLogger()
logging.basicConfig(
    format="%(asctime)s %(module)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
stream_handler = logging.StreamHandler(sys.stdout)
log.addHandler(stream_handler)


def get_build_status(build_id, session):
    _res = session.get(
        f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/build/{build_id}",
        verify=False,
    )
    status = _res.json().get("data")["status"]
    return status


def delete_conda_environments(session):
    existing_envs_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/?namespace=global"
    response = session.get(existing_envs_url, verify=False)
    for env in response.json()["data"]:
        env_name = env["name"]
        delete_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/global/{env_name}"
        log.info(f"Deleting {delete_url}")
        session.delete(delete_url, verify=False)
    log.info("All conda environments deleted.")


@pytest.mark.timeout(10)
def build_n_environments(n, builds, session):
    log.info(f"Building {n} conda environments...")
    for _ in range(n):
        time.sleep(1)
        builds.append(create_conda_store_env(session))
    return builds


def get_deployment_count(client):
    _client = dynamic.DynamicClient(client)
    deployment_api = _client.resources.get(api_version="apps/v1", kind="Deployment")
    deployment = deployment_api.get(
        name="nebari-conda-store-worker", namespace=NAMESPACE
    )
    replica_count = deployment.spec.replicas
    return replica_count


def create_conda_store_env(session):
    _url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/specification/"
    name = str(uuid.uuid4())
    request_json = {
        "namespace": "global",
        "specification": f"dependencies:\n  - tqdm\nvariables: {{}}\nchannels: "
        f"[]\n\ndescription: ''\nname: {name}\nprefix: null",
    }
    response = session.post(_url, json=request_json, verify=False)
    log.debug(request_json)
    log.debug(response.json())
    return response.json()["data"]["build_id"]


def b64encodestr(string):
    return b64encode(string.encode("utf-8")).decode()


@pytest.mark.timeout(20 * 60)
def timed_wait_for_deployments(target_deployment_count, client):
    log.info(
        f"Waiting for deployments to reach target value {target_deployment_count}  ..."
    )
    replica_count = get_deployment_count(client)
    while replica_count != target_deployment_count:
        replica_count = get_deployment_count(client)
        direction = "up" if target_deployment_count > replica_count else "down"
        log.info(
            f"Scaling {direction} deployments: from {replica_count} to {target_deployment_count}"
        )
        time.sleep(5)
    log.info(f"Deployment count: {replica_count}")


@pytest.mark.timeout(6 * 60)
def timed_wait_for_environment_creation(builds, session):
    created_count = 0
    while True:
        _count = len([b for b in builds if get_build_status(b, session) == "COMPLETED"])
        if created_count != _count:
            log.info(f"{_count}/{len(builds)} Environments created")
            created_count = _count
        else:
            log.info("Environment creation finished successfully.")
            return


@pytest.fixture
def requests_session(patched_secret_token):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {patched_secret_token}"})
    yield session
    session.close()


@pytest.fixture
def kubernetes_config():
    yield config.load_kube_config()


@pytest.fixture
def api_client(kubernetes_config):
    with kubernetes.client.ApiClient(kubernetes_config) as _api_client:
        yield _api_client


@pytest.fixture
def patched_secret_token(kubernetes_config, api_client):
    # Create an instance of the API class
    log.info("Creating a admin token for the test.")
    api_instance = kubernetes.client.CoreV1Api(api_client)
    name = "conda-store-secret"  # str | name of the Secret
    elevated_token = str(uuid.uuid4())

    # Get secret
    api_response, secret_config = get_conda_secret(api_instance, name, NAMESPACE)

    # Update secret
    permissions = {
        "primary_namespace": "",
        "role_bindings": {"*/*": ["admin"]},
    }
    secret_config["service-tokens"][elevated_token] = permissions
    api_response.data = {"config.json": b64encodestr(json.dumps(secret_config))}
    log.info(f"Patching secret: {name}.")
    api_instance.patch_namespaced_secret(name, NAMESPACE, api_response)

    # Get pod name for conda-store
    # Restart conda-store server pod
    api_response = api_instance.list_namespaced_pod(NAMESPACE)
    server_pod = [
        i for i in api_response.items if "nebari-conda-store-server-" in i.metadata.name
    ][0]
    log.info(f"Restarting conda-store-server pod: {server_pod.metadata.name}")
    api_instance.delete_namespaced_pod(server_pod.metadata.name, NAMESPACE)
    time.sleep(10)

    yield elevated_token


def get_conda_secret(api_instance, name, namespace):
    api_response = api_instance.read_namespaced_secret(name, namespace)
    api_response_data = api_response.data
    secret_data = api_response_data["config.json"]
    secret_config = json.loads(base64.b64decode(secret_data))
    return api_response, secret_config


# @pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_scale_up_and_down(patched_secret_token, api_client, requests_session):
    builds = []
    _initial_deployment_count = get_deployment_count(api_client)
    log.info(f"Deployments at the start of the test: {_initial_deployment_count}")
    delete_conda_environments(requests_session)
    builds = build_n_environments(TEST_CONDASTORE_WOKER_COUNT, builds, requests_session)
    log.info(
        f"Wait for {TEST_CONDASTORE_WOKER_COUNT} conda-store-worker pods to start."
    )
    timed_wait_for_deployments(
        TEST_CONDASTORE_WOKER_COUNT + _initial_deployment_count, api_client
    )
    timed_wait_for_environment_creation(builds, requests_session)
    log.info(f"Wait till worker deployment scales down to {_initial_deployment_count}")
    timed_wait_for_deployments(_initial_deployment_count, api_client)
    log.info("Test passed.")
    delete_conda_environments(requests_session)
    log.info("Test passed.")
