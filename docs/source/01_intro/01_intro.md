# What is QHub?
Open source tool for data science research, development, and deployment.

QHub is [**Infrastructure as Code**](docs/source/9_faq/1_faqs.html#what-is-infrastructure-as-code-and-how-it-relates-to-qhub)
that simplifies the deployment of data science projects using JupyterHub and Dask Gateway for you and your team.

Designed to simplify the deployment and maintenance of scalable computational platforms in the cloud, QHub is ideal for
organizations that need a shared compute platform that is flexible, accessible, and scalable.

## QHub Technology Stack

![High-level illustration of QHub architecture](../meta_images/qhub-cloud_architecture.png)

### Components

The technology stack is an integration of the following existing open source libraries:

+ [**Terraform**](https://www.terraform.io/intro/index.html) a tool for building, changing, and versioning infrastructure.
+ [**Kubernetes**](https://kubernetes.io/docs/home/) a cloud-agnostic orchestration system
+ [**Helm**](https://helm.sh/): a package manager for Kubernetes
+ [**JupyterHub**](https://jupyter.org/hub): a shareable compute platform for data science
+ [**JupyterLab**](https://jupyterlab.readthedocs.io/en/stable/): a web-based interactive development environment for Jupyter Notebooks
+ [**Dask**](https://docs.dask.org/en/latest/): a scalable and flexible  library for parallel computing in Python
  + [Dask-Gateway](https://gateway.dask.org/): a secure, multi-tenant server for managing Dask clusters
+ [**GitHub Actions**](https://docs.github.com/en/actions): a tool to automate, customize, and execute software
  development workflows in a GitHub repository.

Amongst the newly created open source libraries on the tech stack are:
+ [**KubeSSH**](https://github.com/yuvipanda/kubessh) brings the SSH experience to a modern cluster manager.
+ [**Jupyter-Videochat**](https://github.com/yuvipanda/jupyter-videochat) allows video-chat with JupyterHub peers inside
  JupyterLab, powered by Jitsi.
+ [**conda-store**](https://github.com/quansight/conda-store) serves identical conda environments and controls its life-cycle.
+ [**Conda-Docker**](https://github.com/conda-incubator/conda-docker), an extension to the docker concept of having
  declarative environments that are associated with Docker images allowing tricks and behaviour that otherwise would not be allowed.


# Why use QHub?

QHub provides enables teams to build their own scalable compute infrastructure with:

+ Easy installation and maintenance controlled by a single configuration file.
+ Autoscaling JupyterHub installation deployed on the Cloud provider of your choice.
+ Option to choose from multiple compute instances, such as: **namely normal**, **high memory**, **GPU**, etc.
+ Autoscaling Dask compute clusters for big data using any instance type.
+ Shell access and remote editing access (i.e. VSCode remote) through KubeSSH.
+ Full linux style permissions allowing for different shared folders for different groups of users.
+ Robust compute environment handling allowing both prebuilt and ad-hoc environment creation.
+ Integrated video conferencing, using [Jitsi](https://meet.jit.si/).
