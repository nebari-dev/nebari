import base64
import json
import logging
import sys
import time
import uuid
from unittest import TestCase

import kubernetes.client
import pytest
import requests
from kubernetes import client, config, dynamic
from kubernetes.client import api_client
from kubernetes.client.rest import ApiException
from timeout_function_decorator import timeout

from tests.tests_deployment import constants

CONDA_STORE_API_ENDPOINT = "conda-store/api/v1"

service_permissions = {"primary_namespace": "", "role_bindings": {"*/*": ["admin"]}}

NEBARI_HOSTNAME = constants.NEBARI_HOSTNAME
# NEBARI_HOSTNAME = "pt.quansight.dev" ## Override for local testing


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

    @staticmethod
    def fetch_token():
        v1 = client.CoreV1Api()
        secret = v1.read_namespaced_secret("conda-store-secret", "dev")

        token = [
            k
            for k in json.loads(base64.b64decode(secret.data["config.json"]))[
                "service-tokens"
            ].keys()
        ][0]
        return token

    def read_namespaced_config_map(self):
        with kubernetes.client.ApiClient(self.configuration) as _client:
            api_instance = kubernetes.client.CoreV1Api(_client)
        try:
            api_response = api_instance.read_namespaced_config_map(
                "conda-store-config", "dev"
            )
            return api_response
        except ApiException as e:
            self.log.exception(
                "Exception when calling CoreV1Api->read_namespaced_config_map: %s\n" % e
            )
        finally:
            _client.close()

    def patch_namespaced_config_map(self, config_map):
        with kubernetes.client.ApiClient(self.configuration) as _client:
            api_instance = kubernetes.client.CoreV1Api(_client)
        try:
            api_response = api_instance.patch_namespaced_config_map(
                "conda-store-config", "dev", config_map
            )
            self.log.debug(api_response)
        except ApiException as e:
            self.log.exception(
                "Exception when calling CoreV1Api->patch_namespaced_config_map: %s\n"
                % e
            )
        finally:
            _client.close()

    def setUp(self):
        """
        Get token for conda API.
        Create an API client.
        """
        self.log.info("Setting up the test case.")
        self.configuration = config.load_kube_config()
        # Get token from pre-defined tokens.
        token = self.fetch_token()
        self.headers = {"Authorization": f"Bearer {token}"}

        # Read conda-store-config
        self.config_map = self.read_namespaced_config_map()

        # Patch conda-store-config
        self.config_map.data["conda_store_config.py"] = self.config_map.data[
            "conda_store_config.py"
        ].replace(
            '{default_namespace}/*": {"viewer"}', '{default_namespace}/*": {"admin"}'
        )
        self.patch_namespaced_config_map(self.config_map)

        # Patch conda-store-config

        # Delete existing environments
        self.delete_conda_environments()
        self.log.info("Wait for existing conda-store-worker pods terminate.")
        self.timed_wait_for_deployments(0)
        self.log.info("Ready to start tests.")

    def test_scale_up_and_down(self):
        """
        Crete 5 conda environments.
        Wait for 5 conda-store-worker pods to start.
        Fail if 5 conda-store-worker pods don't spin up in 2 minutes.
        Wait till all the conda environments are created. (max 5 minutes)
        Fail if they don't scale down in another 5 minutes.
        """
        # Crete 5 conda environments.
        count = 5
        self.build_n_environments(count)
        self.log.info("Wait for 5 conda-store-worker pods to start.")
        self.timed_wait_for_deployments(count)
        self.log.info(
            "Waiting (max 5 minutes) for all the conda environments to be created."
        )
        self.timed_wait_for_environment_creation(count)
        self.log.info("Wait till worker deployment scales down to 0")
        self.timed_wait_for_deployments(0)
        self.log.info("Test passed.")

    def tearDown(self):
        """
        Delete all conda environments.
        """
        self.delete_conda_environments()

        # Revert conda-store-config
        self.config_map.data["conda_store_config.py"] = self.config_map.data[
            "conda_store_config.py"
        ].replace(
            '{default_namespace}/*": {"admin"}', '{default_namespace}/*": {"viewer"}'
        )
        self.patch_namespaced_config_map(self.config_map)
        self.log.info("Teardown complete.")
        self.stream_handler.close()

    def delete_conda_environments(self):
        existing_envs_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/?namespace=global"
        response = requests.get(existing_envs_url, headers=self.headers)
        for env in response.json()["data"]:
            env_name = env["name"]
            delete_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/global/{env_name}"
            self.log.info(f"Deleting {delete_url}")
            requests.delete(delete_url, headers=self.headers)
        self.log.info("All conda environments deleted.")

    @timeout(6 * 60)
    def timed_wait_for_environment_creation(self, target_count):
        created_count = 0
        while created_count != target_count:
            created_count = 0
            response = requests.get(
                f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/",
                headers=self.headers,
            )
            for env in response.json().get("data"):
                build_id = env["current_build_id"]
                _res = requests.get(
                    f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/build/{build_id}",
                    headers=self.headers,
                )
                status = _res.json().get("data")["status"]
                if status == "COMPLETED":
                    created_count += 1
            self.log.info(f"{created_count}/{target_count} Environments created")
            time.sleep(5)

        self.log.info("timed_wait_for_environment_creation finished successfully.")

    @timeout(10)
    def build_n_environments(self, n):
        self.log.info(f"Building {n} conda environments...")
        for _ in range(n):
            time.sleep(1)
            self.create_conda_store_env()

    @timeout(10 * 60)
    def timed_wait_for_deployments(self, target_deployment_count):
        self.log.info(
            f"Waiting for deployments to reach target value {target_deployment_count}  ..."
        )
        _client = dynamic.DynamicClient(
            api_client.ApiClient(configuration=self.configuration)
        )
        replica_count = -1
        while replica_count != target_deployment_count:
            deployment_api = _client.resources.get(
                api_version="apps/v1", kind="Deployment"
            )
            deployment = deployment_api.get(
                name="nebari-conda-store-worker", namespace="dev"
            )
            replica_count = deployment.spec.replicas
            direction = "up" if target_deployment_count > replica_count else "down"
            self.log.info(
                f"Scaling {direction} deployments: {replica_count}/{target_deployment_count}"
            )
            time.sleep(5)
        self.log.info(f"Deployment count: {replica_count}")

    def create_conda_store_env(self):
        _url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/specification/"
        name = str(uuid.uuid4())
        request_json = {
            "namespace": "global",
            "specification": f"dependencies:\n  - pandas\nvariables: {{}}\nchannels: "
            f"[]\n\ndescription: ''\nname: {name}\nprefix: null",
        }
        response = requests.post(_url, json=request_json, headers=self.headers)
        self.log.debug(request_json)
        self.log.debug(self.headers)
        self.log.debug(response.json())
        return response.json()["data"]["build_id"]
