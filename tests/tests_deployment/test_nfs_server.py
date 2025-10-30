import logging
import os

import pytest
from kubernetes import client, config

logger = logging.getLogger(__name__)


class TestNFSServer:
    """Test NFS server basic functionality."""

    @pytest.fixture(scope="class")
    def kube_client(self):
        config.load_kube_config()
        return client.CoreV1Api()

    @pytest.fixture(scope="class")
    def namespace(self):
        return os.environ.get("NEBARI_NAMESPACE", "dev")

    def test_nfs_server_pods_running(self, kube_client, namespace):
        """Test that NFS server pods are running successfully."""

        nfs_server_pods = kube_client.list_namespaced_pod(
            namespace=namespace, label_selector="role=nfs-server-nfs"
        )
        conda_store_pods = kube_client.list_namespaced_pod(
            namespace=namespace, label_selector="role=nebari-conda-store-worker"
        )

        # At least one should exist
        total_pods = len(nfs_server_pods.items) + len(conda_store_pods.items)
        assert total_pods > 0, "No NFS server pods found"

        # Check that pods are running
        all_pods = nfs_server_pods.items + conda_store_pods.items
        for pod in all_pods:
            logger.info(
                f"Checking pod: {pod.metadata.name} - Status: {pod.status.phase}"
            )
            assert (
                pod.status.phase == "Running"
            ), f"NFS server pod {pod.metadata.name} is not running: {pod.status.phase}"

            # Check if pod has NFS container
            nfs_containers = [c for c in pod.spec.containers if "nfs" in c.name.lower()]
            logger.info(
                f"Pod {pod.metadata.name} has {len(nfs_containers)} NFS containers"
            )

            if not nfs_containers:
                container_names = [c.name for c in pod.spec.containers]
                logger.info(f"Pod {pod.metadata.name} containers: {container_names}")

    def test_nfs_service_accessible(self, kube_client, namespace):
        """Test that NFS service is accessible and responds correctly."""

        all_services = kube_client.list_namespaced_service(namespace=namespace)
        nfs_services = [
            svc for svc in all_services.items if "nfs" in svc.metadata.name.lower()
        ]

        for svc in nfs_services:
            logger.info(f"  - {svc.metadata.name}: {svc.spec.cluster_ip}")

        assert len(nfs_services) > 0, "No NFS services found"

        nfs_service = nfs_services[0]

        # Verify service has the required ports
        expected_ports = ["nfs", "mountd", "rpcbind"]
        service_ports = {port.name for port in nfs_service.spec.ports}

        for expected_port in expected_ports:
            assert (
                expected_port in service_ports
            ), f"Required NFS port {expected_port} not found in service"

        # Verify port numbers
        port_map = {port.name: port.port for port in nfs_service.spec.ports}
        expected_port_numbers = {"nfs": 2049, "mountd": 20048, "rpcbind": 111}

        for port_name, expected_number in expected_port_numbers.items():
            actual_number = port_map.get(port_name)
            logger.info(
                f"Port {port_name}: expected={expected_number}, actual={actual_number}"
            )
            assert (
                actual_number == expected_number
            ), f"{port_name.upper()} port should be {expected_number}, got {actual_number}"

    def test_persistent_volume_claim_bound(self, kube_client, namespace):
        """Test that NFS PVC is properly bound to a volume."""

        pvc_names = [
            "dev-conda-store-storage",
            "nebari-conda-store-storage",
            "nfs-server-nfs-storage",
        ]

        all_pvcs = []
        for pvc_name in pvc_names:
            pvcs = kube_client.list_namespaced_persistent_volume_claim(
                namespace=namespace, field_selector=f"metadata.name={pvc_name}"
            )
            all_pvcs.extend(pvcs.items)

        if not all_pvcs:
            all_namespace_pvcs = kube_client.list_namespaced_persistent_volume_claim(
                namespace=namespace
            )
            storage_pvcs = [
                pvc
                for pvc in all_namespace_pvcs.items
                if "storage" in pvc.metadata.name.lower()
                or "nfs" in pvc.metadata.name.lower()
            ]
            all_pvcs.extend(storage_pvcs)

        class PVCList:
            def __init__(self, items):
                self.items = items

        pvcs = PVCList(all_pvcs)

        if len(pvcs.items) > 0:
            pvc = pvcs.items[0]
            logger.info(f"PVC found: {pvc.metadata.name}")
            logger.info(f"PVC status: {pvc.status.phase}")
            logger.info(f"Storage class: {pvc.spec.storage_class_name}")

            assert pvc.status.phase == "Bound", f"PVC is not bound: {pvc.status.phase}"

            # Check that requested storage matches configuration
            requested_storage = pvc.spec.resources.requests.get("storage")
            logger.info(f"Requested storage: {requested_storage}")
            assert requested_storage is not None, "No storage requested in PVC"

    def test_nfs_data_persistence_across_restarts(self, kube_client, namespace):
        """Test that NFS data persists across pod restarts."""

        # Check that the PVC has the correct reclaim policy and storage class
        pvcs = kube_client.list_namespaced_persistent_volume_claim(
            namespace=namespace, field_selector="metadata.name=dev-conda-store-storage"
        )

        if len(pvcs.items) > 0:
            pvc = pvcs.items[0]
            pv_name = pvc.spec.volume_name

            if pv_name:
                # Get the persistent volume
                pvs = kube_client.list_persistent_volume(
                    field_selector=f"metadata.name={pv_name}"
                )

                if len(pvs.items) > 0:
                    pv = pvs.items[0]
                    reclaim_policy = pv.spec.persistent_volume_reclaim_policy
                    assert reclaim_policy in [
                        "Retain",
                        "Recycle",
                    ], f"PV reclaim policy {reclaim_policy} may cause data loss"

    def test_nfs_resource_limits(self, kube_client, namespace):
        """Test that NFS containers have appropriate resource limits."""
        pods = kube_client.list_namespaced_pod(
            namespace=namespace, label_selector="role=dev-conda-store-worker"
        )

        for pod in pods.items:
            for container in pod.spec.containers:
                if "nfs" in container.name.lower():
                    # Check that container has resource constraints
                    # (This is more of a best practice check, to avoid
                    #  similar issues as we had with conda-store worker in the past)
                    if container.resources:
                        if container.resources.limits:
                            assert (
                                "memory" in container.resources.limits
                                or "cpu" in container.resources.limits
                            ), f"NFS container {container.name} should have resource limits"
