import os

from diagrams.custom import Custom

from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Pod
from diagrams.k8s.storage import PersistnetVolume as PersistentVolume

from diagrams.gcp.network import LoadBalancing


def custom_icon(filename):
    return os.path.join('architecture/icons', filename)


with Diagram("QHub Architecture: High Level", filename='high_level_architecture', show=False, direction="TB",):
    with Cluster('Kubernetes Cluster'):
        conda_pvc = PersistentVolume('Conda (Persistent Volume)')
        nfs_pvc = PersistentVolume('NFS (Persistent Volume)')
        elb = LoadBalancing('Ingress')

        with Cluster("Pods"):
            dask_gateway = Custom('Dask Gateway', custom_icon('dask.png'))
            jupyterhub = Custom('JupyterHub', custom_icon('jupyter_hub.png'))
            dask_scheduler = Custom('Dask Scheduler', custom_icon('dask.png'))
            nfs_server = Pod('NFS Server')
            conda_store = Custom('Conda Store', custom_icon('conda.png'))
            nginx = Custom('Nginx', custom_icon('nginx.png'))

    nginx >> elb
    nginx >> jupyterhub
    [nfs_server, conda_store, dask_gateway] << jupyterhub
    [conda_store, dask_scheduler] << dask_gateway
    nfs_server >> nfs_pvc
    conda_store >> conda_pvc
