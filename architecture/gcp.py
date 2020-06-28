from architecture.common import get_common_architecture

gcp_architecture = get_common_architecture(
    cloud_provider="Google Cloud Platform",
    filename="qhub_gcp_architecture",
    container_registry="GCR",
    k8s_cluster_name="'Kubernetes Cluster'",
    k8s_engine_name="GKE"
)
