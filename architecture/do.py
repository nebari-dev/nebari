from architecture.common import get_common_architecture

do_architecture = get_common_architecture(
    cloud_provider="Digital Ocean",
    filename="qhub_do_architecture",
    container_registry="DockerHub",
    k8s_cluster_name="'Kubernetes Cluster'",
    k8s_engine_name="Kubernetes Engine",
)
