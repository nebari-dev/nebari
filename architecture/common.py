from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Pod
from diagrams.k8s.infra import Node
from diagrams.k8s.ecosystem import Helm
from diagrams.k8s.storage import PersistnetVolume as PersistentVolume

from diagrams.gcp.devtools import ContainerRegistry
from diagrams.gcp.compute import KubernetesEngine
from diagrams.gcp.network import LoadBalancing


def get_common_architecture(
        cloud_provider,
        filename,
        container_registry,
        k8s_cluster_name,
        k8s_engine_name
):
    with Diagram(f"QHub Architecture: {cloud_provider}", filename=f'{filename}', show=False, direction="TB",):
        with Cluster(cloud_provider):
            gcr = ContainerRegistry(container_registry)
            with Cluster(k8s_cluster_name):
                kube_engine = KubernetesEngine(k8s_engine_name)

                conda_pvc = PersistentVolume('Conda')
                nfs_pvc = PersistentVolume('NFS')
                elb = LoadBalancing('Ingress')

                with Cluster('Master'):
                    general = Node('general')
                    Node('user')
                    Node('worker')
                    general << kube_engine

                with Cluster("Pods"):
                    dask_gateway = Pod('Dask Gateway')
                    jupyterhub = Pod('JupyterHub')
                    dask_scheduler = Pod('Dask Scheduler')
                    nfs_server = Pod('NFS Server')
                    conda_store = Pod('Conda Store')
                    nginx = Pod('Nginx')
                    Pod('Cert Manager')
                    image_puller = Pod('Image Puller')

        nginx >> elb
        nginx >> jupyterhub
        [nfs_server, conda_store, dask_gateway] << jupyterhub
        [conda_store, dask_scheduler] << dask_gateway
        image_puller >> gcr
        nfs_server >> nfs_pvc
        conda_store >> conda_pvc
        Helm('Helm') >> kube_engine
