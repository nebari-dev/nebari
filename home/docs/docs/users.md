# QHub for Teams

Efficient data-driven teams take full advantage of distributed computing without worrying about its maintenance. The user is provided the Jupyter platform interface while QHub handles all the complexities of [**Kubernetes**](https://kubernetes.io/docs/home/), a cloud-agnostic and open source orchestration system for managing containerized workloads and services for deployments. QHub uses Kubernetes architecture on the backend for cloud computing that works seamlessly with the cloud provider of your choice.

## **Why Your Team Should Use QHub**

### The Solution

QHub is the tool for teams that experience many of the pain points of doing data science and want to seamlessly on the cloud with minimal maintenance. QHub offers a robust data science environment that can be easily tailored to suit your organization's needs.


### The Problem

Data scientists often have to circumvent limitations of the tools and platforms they use for distributed computing. Most of their energy is spent trying to manage unstable development environments, deciphering cloud specific details, and suffering from unsuccessful, as well as costly, deployments, keeping up with constantly changing tooling, resolving package conflicts, and handling authentication problems among others.

The creators of QHub are data scientsits and DevOps engineers, who have experienced such highly common frustrations on a daily basis and decided to work towards creating an open source tool that answers the need for seamless distributed computing and deployment.


### QHub Architecture

The QHub architecture, operating on the familiar Jupyter interface, brings together some of the most efficient components of data science and cloud deployment. Here is a high level description of the components that QHub brings to the user:

+ **QHub makes Dask a fully integrated part of its architecture**

  + Integration of [**Dask Gateway**](https://gateway.dask.org/) allows users to use Dask clusters in a shared, centrally managed cluster environment, without requiring users to have direct access to the underlying cluster backend, such as Kubernetes.
  + Multifunctionality of [**Dask Scheduler**](https://docs.dask.org/en/latest/scheduler-overview.html) allows scheduling and computing tasks either on a single machine or in a distributed cluster.

+ [**Conda**](https://docs.conda.io/en/latest/) **as an integral part of QHub's architectural design**

  + [**Conda Environments**](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) enables the user to create their custom environments tailored for their teams' needs. QHub uses a new approach to distributed environments by using [**conda-store**](https://github.com/quansight/conda-store). Environment creation is independent from [**docker container**](https://www.docker.com/resources/what-container) creations which provides a substantial benefit in speed. [**Dask workers**](https://distributed.dask.org/en/latest/worker.html) can use any environment.

+ **Kubernetes behind the scene**

  + [**Network File System (NFS)**](https://en.wikipedia.org/wiki/Network_File_System) protocol is one of the ways Kubernetes allows applications to access storage.
  + A [**Kubernetes Volume**](https://kubernetes.io/docs/concepts/storage/volumes/) is just a directory, possibly with some data in it, which is accessible to the [**Containers**](https://kubernetes.io/docs/concepts/containers/) in a [**Kubernetes Pod**](https://kubernetes.io/docs/concepts/workloads/pods/pod/).
  + Running containers together in a pod often makes file share between those containers a necessity. Files in a container are ephemeral, which means if a container crashes, [**kubelet**](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/#:~:text=Synopsis,object%20that%20describes%20a%20pod) will restart the container, however, the files will not be preserved. The [**Kubernetes Volume**](https://kubernetes.io/docs/concepts/storage/volumes/#types-of-volumes) abstraction solves this problem.
  + NFS shares files directly from a container in a Kubernetes Pod, and sets up a [**Kubernetes Persistent Volume**](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) accessed via NFS.
  + Kubernetes has a built‑in configuration for HTTP load balancing, called [**Ingress**](https://kubernetes.io/docs/concepts/services-networking/ingress/) that defines and controls the rules for external connectivity to Kubernetes services.
    + Users who need to provide external access to their KuberneteQ|Hube type, namely normal, high memory, and GPU.

### How to Create Conda Environments on QHub

QHub enables you to customize environments for your needs and share them with other users in your team without worrying about stability or conflicts. This feature allows the deployment of a scalable cloud-agnostic compute environment suitable for teams.

With QHub, you can create and handle both prebuilt and ad-hoc conda environments in a robust way. To learn how to create conda environments, please visit [this page](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

+ **Distributing a conda environment with `conda-store` on QHub**
  + QHub is experimenting with a new way of distributing environments using [**conda-store**](https://github.com/quansight/conda-store). `conda-store` declaratively builds conda environments by watching a directory of `environment.yaml` files.

  + Each environment configuration is a `environment.<filename>`, mapping to a conda environment definition file. If you need to pin a specific version, you should include it in the definition. Upon changing an environment definition, you should expect 1-10 minutes upon deployment of the configuration for the environment to appear.

  + `conda-store` environments currently require each environment to include the following packages and versions:

        ipykernel
        ipywidgets
        dask==2.14.0
        distributed==2.14.0
        dask-gateway==0.6.1

### How to Authenticate Users

QHub authentication can be done using `Auth0` and `Github` and including the type of authentication in the provided configuration file template.

+ To configure the authentication for your cloud deployment, navigate to the security section in the provided configuration file template, seen below:

        security:
        authentication:
            type: GitHub
            config:
                client_id: <CLIENT_ID>
                client_secret: <CLIENT_SECRET>
                oauth_callback_url: <https://jupyter.do.qhub.dev/hub/oauth_callback>
        users:
            username:
                uid: 1000
                primary_group: users
            username:
                uid: 1001
                primary_group: admin
        groups:
            users:
                gid: 100
            admin:
                gid: 101

Fill in the section with your cloud account credentials and authentication type (`Github` or `Auth0`) for configuring security for your qhub deployment.
