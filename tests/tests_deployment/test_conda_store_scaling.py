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

from base64 import b64encode
from contextlib import contextmanager


def b64encodestr(string):
    return b64encode(string.encode("utf-8")).decode()


@contextmanager
def patched_secret_token(configuration):

    try:
        with kubernetes.client.ApiClient(configuration) as api_client:
            # Create an instance of the API class
            api_instance = kubernetes.client.CoreV1Api(api_client)
            name = "conda-store-secret"  # str | name of the Secret
            namespace = "dev"  # str | object name and auth scope, such as for teams and projects
            elevated_token = str(uuid.uuid4())

            try:
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
                api_response.data = {
                    "config.json": b64encodestr(json.dumps(secret_config))
                }
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

                yield elevated_token

                # Get update secret
                api_response = api_instance.read_namespaced_secret(name, namespace)
                api_response_data = api_response.data
                secret_data = api_response_data["config.json"]
                secret_config = json.loads(base64.b64decode(secret_data))

                # Update secret
                secret_config["service-tokens"].pop(elevated_token)
                api_response.data = {
                    "config.json": b64encodestr(json.dumps(secret_config))
                }
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

            except ApiException as e:
                print(
                    "Exception when calling CoreV1Api->read_namespaced_secret: %s\n" % e
                )
    finally:
        # api_response_data["config.json"]["service-tokens"].pop(elevated_token)
        # api_response = api_instance.patch_namespaced_secret(name, namespace, api_response_data)
        pass


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
        self.log.info(f"Conda store config patched: {config_map}")
        with kubernetes.client.ApiClient(self.configuration) as _client:
            api_instance = kubernetes.client.CoreV1Api(_client)
        try:
            api_response = api_instance.patch_namespaced_config_map(
                "conda-store-config", "dev", config_map
            )
            self.log.info(api_response)
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

    def test_scale_up_and_down(self):
        """
        Crete 5 conda environments.
        Wait for 5 conda-store-worker pods to start.
        Fail if 5 conda-store-worker pods don't spin up in 2 minutes.
        Wait till all the conda environments are created. (max 5 minutes)
        Fail if they don't scale down in another 5 minutes.
        """
        with patched_secret_token(self.configuration) as token:
            self.headers = {"Authorization": f"Bearer {token}"}
            self.initial_deployment_count = self.get_deployment_count()
            self.delete_conda_environments()
            count = 5
            self.build_n_environments(count)
            self.log.info("Wait for 5 conda-store-worker pods to start.")
            self.timed_wait_for_deployments(count)
            self.log.info(
                "Waiting (max 5 minutes) for all the conda environments to be created."
            )
            self.timed_wait_for_environment_creation(count)
            self.log.info("Wait till worker deployment scales down to 0")
            self.timed_wait_for_deployments(self.initial_deployment_count)
            self.log.info("Test passed.")
            self.delete_conda_environments()

    def tearDown(self):
        """
        Delete all conda environments.
        """
        self.log.info("Teardown complete.")
        self.stream_handler.close()
        pass

    def delete_conda_environments(self):
        existing_envs_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/?namespace=global"
        response = requests.get(existing_envs_url, headers=self.headers, verify=False)
        for env in response.json()["data"]:
            env_name = env["name"]
            delete_url = f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/global/{env_name}"
            self.log.info(f"Deleting {delete_url}")
            requests.delete(delete_url, headers=self.headers, verify=False)
        self.log.info("All conda environments deleted.")

    @timeout(6 * 60)
    def timed_wait_for_environment_creation(self, target_count):
        created_count = 0
        while created_count <= target_count:
            created_count = 0
            response = requests.get(
                f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/environment/?namespace=global",
                headers=self.headers,
                verify=False,
            )
            for env in response.json().get("data"):
                build_id = env["current_build_id"]
                _res = requests.get(
                    f"https://{NEBARI_HOSTNAME}/{CONDA_STORE_API_ENDPOINT}/build/{build_id}",
                    headers=self.headers,
                    verify=False,
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

    @timeout(15 * 60)
    def timed_wait_for_deployments(self, target_deployment_count):
        self.log.info(
            f"Waiting for deployments to reach target value {target_deployment_count}  ..."
        )
        replica_count = self.get_deployment_count()
        while replica_count != target_deployment_count:
            replica_count = self.get_deployment_count()
            direction = "up" if target_deployment_count > replica_count else "down"
            self.log.info(
                f"Scaling {direction} deployments: {replica_count}/{target_deployment_count}"
            )
            time.sleep(5)
        self.log.info(f"Deployment count: {replica_count}")

    def get_deployment_count(self):
        _client = dynamic.DynamicClient(
            api_client.ApiClient(configuration=self.configuration)
        )
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
        response = requests.post(
            _url, json=request_json, headers=self.headers, verify=False
        )
        self.log.info(request_json)
        self.log.info(self.headers)
        self.log.info(response.json())
        return response.json()["data"]["build_id"]
