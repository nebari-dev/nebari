from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Pod
from diagrams.k8s.infra import Node
from diagrams.k8s.ecosystem import Helm
from diagrams.k8s.storage import PersistnetVolume as PersistentVolume

from diagrams.aws.compute import ElasticKubernetesService, EC2ContainerRegistry
from diagrams.aws.network import VPC, InternetGateway, ElasticLoadBalancing
from diagrams.aws.storage import ElasticFileSystemEFS
from diagrams.aws.compute import ApplicationAutoScaling


with Diagram(
    "QHub Architecture: AWS",
    filename="qhub_aws_architecture",
    show=False,
    direction="TB",
):
    with Cluster("AWS Cloud"):
        ecr = EC2ContainerRegistry("ECR")
        with Cluster("VPC"):
            vpc = VPC("vpc")

            with Cluster("Subnet (Multiple Availability Zones)"):
                efs = ElasticFileSystemEFS("EFS")
                with Cluster("Kubernetes Cluster"):
                    eks = ElasticKubernetesService("EKS")
                    eks - ApplicationAutoScaling("Auto Scaling")

                    k8s_vol = PersistentVolume("NFS")
                    k8s_vol >> efs

                    with Cluster("Public"):
                        ig = InternetGateway("Internet gateway")
                        elb = ElasticLoadBalancing("Ingress")
                        public = [ig, elb]
                        elb >> ecr

                    with Cluster("Master"):
                        general = Node("general")
                        user = Node("user")
                        worker = Node("worker")
                        general << eks

                    with Cluster("Pods"):
                        dask_gateway = Pod("Dask Gateway")
                        jupyterhub = Pod("JupyterHub")
                        dask_scheduler = Pod("Dask Scheduler")
                        nfs_server = Pod("NFS Server")
                        conda_store = Pod("Conda Store")
                        nginx = Pod("Nginx")
                        cert_manager = Pod("Cert Manager")
                        image_puller = Pod("Image Puller")

    nginx >> jupyterhub
    [nfs_server, conda_store, dask_gateway] << jupyterhub
    [conda_store, dask_scheduler] << dask_gateway
    [image_puller, nginx] >> elb
    nfs_server >> k8s_vol
    Helm("Helm") >> eks
