import base64
import json
import logging
import os
import sys
import time
import uuid
from unittest import TestCase

import kubernetes.client
import pytest
import requests
from kubernetes import config, dynamic
from timeout_function_decorator import timeout

from tests.tests_deployment import constants

CONDA_STORE_API_ENDPOINT = "conda-store/api/v1"
NEBARI_HOSTNAME = constants.NEBARI_HOSTNAME
# NEBARI_HOSTNAME = "pt.quansight.dev" ## Override for local testing

from base64 import b64encode
from contextlib import contextmanager


def b64encodestr(string):
    return b64encode(string.encode("utf-8")).decode()


@contextmanager
def patched_secret_token(configuration):

    with kubernetes.client.ApiClient(configuration) as _api_client:
        # Create an instance of the API class
        api_instance = kubernetes.client.CoreV1Api(_api_client)
        name = "conda-store-secret"  # str | name of the Secret
        namespace = (
            "dev"  # str | object name and auth scope, such as for teams and projects
        )
        elevated_token = str(uuid.uuid4())

        # Get secret
        api_response = api_instance.read_namespaced_secret(name, namespace)
        api_response_data = api_response.data
        secret_data = api_response_data["config.json"]
        secret_config = json.loads(base64.b64decode(secret_data))

        # Update secret
        permissions = {
            "primary_namespace": "",
            "role_bindings": {"*/*": ["admin"]},
        }
        secret_config["service-tokens"][elevated_token] = permissions
        api_response.data = {"config.json": b64encodestr(json.dumps(secret_config))}
        api_patch_response = api_instance.patch_namespaced_secret(
            name, namespace, api_response
        )

        # Get pod name for conda-store
        # Restart conda-store server pod
        print(api_patch_response)
        api_response = api_instance.list_namespaced_pod(namespace)
        server_pod = [
            i
            for i in api_response.items
            if "nebari-conda-store-server-" in i.metadata.name
        ][0]
        api_instance.delete_namespaced_pod(server_pod.metadata.name, namespace)
        time.sleep(10)

        yield elevated_token, _api_client

        # Get update secret
        api_response = api_instance.read_namespaced_secret(name, namespace)
        api_response_data = api_response.data
        secret_data = api_response_data["config.json"]
        secret_config = json.loads(base64.b64decode(secret_data))

        # Update secret
        secret_config["service-tokens"].pop(elevated_token)
        api_response.data = {"config.json": b64encodestr(json.dumps(secret_config))}
        api_patch_response = api_instance.patch_namespaced_secret(
            name, namespace, api_response
        )

        # Get pod name for conda-store
        # Restart conda-store server pod
        print(api_patch_response)
        api_response = api_instance.list_namespaced_pod(namespace)
        server_pod = [
            i
            for i in api_response.items
            if "nebari-conda-store-server-" in i.metadata.name
        ][0]
        api_instance.delete_namespaced_pod(server_pod.metadata.name, namespace)


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("error")
class TestCondaStoreWorkerHPA(TestCase):
    """
    Creates 5 conda environments.
    Check conda-store-worker Scale up to 5 nodes.
    Check conda-store-worker Scale down to 0 nodes.
    """

    log = logging.getLogger()
    logging.basicConfig(
        format="%(asctime)s %(module)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.INFO,
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    log.addHandler(stream_handler)

    def setUp(self):
        """
        Get token for conda API.
        Create an API client.
        """
        self.log.info("Setting up the test case.")
        self.configuration = config.load_kube_config()
        self.request_session = requests.Session()
        self.builds = []
        self.count = os.getenv("TEST_CONDASTORE_WOKER_COUNT", 5)

    def test_scale_up_and_down(self):
        """
        Crete 5 conda environments.
        Wait for 5 conda-store-worker pods to start.
        Fail if 5 conda-store-worker pods don't spin up in 2 minutes.
        Wait till all the conda environments are created. (max 5 minutes)
        Fail if they don't scale down in another 5 minutes.
        """
        with patched_secret_token(self.configuration) as (token, _api_client):
            self.request_session.headers.update({"Authorization": f"Bearer {token}"})
            _initial_deployment_count = self.get_deployment_count(_api_client)
            self.log.info(
                f"Deployments at the start of the test: {_initial_deployment_count}"
            )
            self.delete_conda_environments()
            self.build_n_environments(self.count)
            self.log.info("Wait for 5 conda-store-worker pods to start.")
            self.timed_wait_for_deployments(
                self.count + _initial_deployment_count, _api_client
            )
            self.log.info(
                "Waiting (max 5 minutes) for all the conda environments to be created."
            )
            self.timed_wait_for_environment_creation()
            self.log.info(f"Wait till worker deployment scales down to {_initial_deployment_count}")
            self.timed_wait_for_deployments(_initial_deployment_count, _api_client)
            self.log.info("Test passed.")
            self.delete_conda_environments()
        self.log.info("Test passed.")

    def tearDown(self):
        """
        Delete all conda environments.
        """
        self.log.info("Teardown complete.")
        self.stream_handler.close()
        self.request_session.close()
        print("All done.")

    def delete_conda_environments(self):
        existing_envs_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/?namespace=global"
        response = self.request_session.get(existing_envs_url, verify=False)
        for env in response.json()["data"]:
            env_name = env["name"]
            delete_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/global/{env_name}"
            self.log.info(f"Deleting {delete_url}")
            self.request_session.delete(delete_url, verify=False)
        self.log.info("All conda environments deleted.")

    def get_build_status(self, build_id):
        _res = self.request_session.get(
            f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/build/{build_id}",
            verify=False,
        )
        status = _res.json().get("data")["status"]
        return status

    @timeout(6 * 60)
    def timed_wait_for_environment_creation(self, target_count):
        created_count = 0
        while created_count <= target_count:
            created_count = 0
            response = self.request_session.get(
                f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/?namespace=global",
                verify=False,
            )
            for env in response.json().get("data"):
                build_id = env["current_build_id"]
                _res = self.request_session.get(
                    f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/build/{build_id}",
                    verify=False,
                )
                status = _res.json().get("data")["status"]
                if status == "COMPLETED":
                    created_count += 1
            self.log.info(f"{created_count}/{target_count} Environments created")

    @timeout(6 * 60)
    def timed_wait_for_environment_creation(self):
        created_count = 0
        while True:
            _count = len(
                [b for b in self.builds if self.get_build_status(b) == "COMPLETED"]
            )
            if created_count != _count:
                self.log.info(f"{_count}/5 Environments created")
                created_count = _count
            else:
                self.log.info("Environment creation finished successfully.")
                return

    @timeout(10)
    def build_n_environments(self, n):
        self.log.info(f"Building {n} conda environments...")
        for _ in range(n):
            time.sleep(1)
            self.builds.append(self.create_conda_store_env())

    @timeout(15 * 60)
    def timed_wait_for_deployments(self, target_deployment_count, client):
        self.log.info(
            f"Waiting for deployments to reach target value {target_deployment_count}  ..."
        )
        replica_count = self.get_deployment_count(client)
        while replica_count != target_deployment_count:
            replica_count = self.get_deployment_count(client)
            direction = "up" if target_deployment_count > replica_count else "down"
            self.log.info(
                f"Scaling {direction} deployments: from {replica_count} to {target_deployment_count}"
            )
            time.sleep(5)
        self.log.info(f"Deployment count: {replica_count}")

    def get_deployment_count(self, client):
        _client = dynamic.DynamicClient(client)
        deployment_api = _client.resources.get(api_version="apps/v1", kind="Deployment")
        deployment = deployment_api.get(
            name="nebari-conda-store-worker", namespace="dev"
        )
        replica_count = deployment.spec.replicas
        return replica_count

    def create_conda_store_env(self):
        _url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/specification/"
        name = str(uuid.uuid4())
        request_json = {
            "namespace": "global",
            "specification": f"dependencies:\n  - pandas\nvariables: {{}}\nchannels: "
            f"[]\n\ndescription: ''\nname: {name}\nprefix: null",
        }
        response = self.request_session.post(_url, json=request_json, verify=False)
        self.log.info(request_json)
        self.log.info(response.json())
        return response.json()["data"]["build_id"]
