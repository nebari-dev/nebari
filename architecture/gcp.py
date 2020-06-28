from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Pod
from diagrams.k8s.infra import Node
from diagrams.k8s.ecosystem import Helm
from diagrams.k8s.storage import PersistnetVolume as PersistentVolume

from diagrams.gcp.devtools import ContainerRegistry
from diagrams.gcp.compute import KubernetesEngine
from diagrams.gcp.network import LoadBalancing


with Diagram("QHub Architecture: GCP", filename='qhub_gcp_architecture', show=False, direction="TB",):
    with Cluster('Google Cloud Platform'):
        gcr = ContainerRegistry('GCR')
        with Cluster('Kubernetes Cluster'):
            eks = KubernetesEngine('GKE')

            conda_pvc = PersistentVolume('Conda')
            nfs_pvc = PersistentVolume('NFS')
            elb = LoadBalancing('Ingress')

            with Cluster('Master'):
                general = Node('general')
                user = Node('user')
                worker = Node('worker')
                general << eks

            with Cluster("Pods"):
                dask_gateway = Pod('Dask Gateway')
                jupyterhub = Pod('JupyterHub')
                dask_scheduler = Pod('Dask Scheduler')
                nfs_server = Pod('NFS Server')
                conda_store = Pod('Conda Store')
                nginx = Pod('Nginx')
                cert_manager = Pod('Cert Manager')
                image_puller = Pod('Image Puller')

    nginx >> elb
    nginx >> jupyterhub
    [nfs_server, conda_store, dask_gateway] << jupyterhub
    [conda_store, dask_scheduler] << dask_gateway
    image_puller >> gcr
    nfs_server >> nfs_pvc
    conda_store >> conda_pvc
    Helm('Helm') >> eks
