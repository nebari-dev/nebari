# Deploy QHub to an existing kubernetes cluster

If you have an existing kubernetes cluster running in the cloud and would like to deploy QHub on the same cluster, this
is the guide for you.

To illustrate how this is done, the guide walks through a simple example. The guide below is meant to serve as a
reference, the setup of your existing kubernetes might differ rending some of these additional setups steps unnecessary.

## Deploy QHub to an existing AWS EKS cluster

In this example, there already exists a basic web app running on an EKS cluster.
[Here is the tutorial on how to setup this particular Guestbook web app](https://logz.io/blog/amazon-eks-cluster/).

The existing EKS cluster has one VPC with three subnets (each in their own Availability Zone) and no node groups. There
are three nodes each running on a `t3.medium` EC2 instance, unfortunately QHub's `general` node group requires a more
powerful instance type.

Now create three new node groups in preparation for the incoming QHub deployment. Before proceeding, ensure the
following:

- that the subnets can
  ["automatically assign public IP addresses to instances launched into it"](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ip-addressing.html#subnet-public-ip)
- there exists an IAM role with the following permissions:
  - AmazonEKSWorkerNodePolicy

  - AmazonEC2ContainerRegistryReadOnly

  - AmazonEKS_CNI_Policy

  - The following custom policy:

    <details>

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "eksWorkerAutoscalingAll",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeLaunchTemplateVersions",
                    "autoscaling:DescribeTags",
                    "autoscaling:DescribeLaunchConfigurations",
                    "autoscaling:DescribeAutoScalingInstances",
                    "autoscaling:DescribeAutoScalingGroups"
                ],
                "Resource": "*"
            },
            {
                "Sid": "eksWorkerAutoscalingOwn",
                "Effect": "Allow",
                "Action": [
                    "autoscaling:UpdateAutoScalingGroup",
                    "autoscaling:TerminateInstanceInAutoScalingGroup",
                    "autoscaling:SetDesiredCapacity"
                ],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "autoscaling:ResourceTag/k8s.io/cluster-autoscaler/enabled": [
                            "true"
                        ],
                        "autoscaling:ResourceTag/kubernetes.io/cluster/eaeeks": [
                            "owned"
                        ]
                    }
                }
            }
        ]
    }
    ```

    </details>

### Create node groups

Skip this step if node groups already exist.

For AWS,
[follow this guide to create new node groups](https://docs.aws.amazon.com/eks/latest/userguide/create-managed-node-group.html).
Be sure to fill in the following fields carefully:

- "Node Group configuration"
  - `Name` must be either `general`, `user` or `worker`
  - `Node IAM Role` must be the IAM role described proceeding
- "Node Group compute configuration"
  - `Instance type`
    - The recommended minimum vCPU and memory for a `general` node is 8 vCPU / 32 GB RAM
    - The recommended minimum vCPU and memory for a `user` and `worker` node is 4 vCPU / 16 GB RAM
  - `Disk size`
    - The recommended minimum is 200 GB for the attached EBS (block-strage)
- "Node Group scaling configuration"
  - `Minimum size` and `Maximum size` of 1 for the `general` node group
- "Node Group subnet configuration"
  - `subnet` include all existing EKS subnets

## Deploy QHub to Existing EKS Cluster

Ensure that you are using the existing cluster's `kubectl` context.

Initialize in the usual manner:

```
python -m qhub init aws --project <project_name> --domain <domain_name> --ci-provider github-actions --auth-provider github --auth-auto-provision
```

Then update the `qhub-config.yaml` file. The important keys to update are:

- Replace `provider: aws` with `provider: local`
- Replace `amazon_web_services` with `local`
  - And update the `node_selector` and `kube_context` appropriately

<details>

```
project_name: <project_name>
provider: local
domain: <domain_name>
certificate:
  type: self-signed
security:
  authentication:
    type: GitHub
    config:
      client_id:
      client_secret:
      oauth_callback_url: https://<domain_name>/hub/oauth_callback
default_images:
  jupyterhub: quansight/qhub-jupyterhub:v0.3.13
  jupyterlab: quansight/qhub-jupyterlab:v0.3.13
  dask_worker: quansight/qhub-dask-worker:v0.3.13
storage:
  conda_store: 60Gi
  shared_filesystem: 100Gi
theme:
  jupyterhub:
    hub_title: QHub - eaeexisting
    hub_subtitle: Autoscaling Compute Environment on Amazon Web Services
    welcome: Welcome to eaeexisting.qhub.dev. It's maintained by <a href="http://quansight.com">Quansight
      staff</a>. The hub's configuration is stored in a github repository based on
      <a href="https://github.com/Quansight/qhub/">https://github.com/Quansight/qhub/</a>.
      To provide feedback and report any technical problems, please use the <a href="https://github.com/Quansight/qhub/issues">github
      issue tracker</a>.
    logo: /hub/custom/images/jupyter_qhub_logo.svg
    primary_color: '#4f4173'
    secondary_color: '#957da6'
    accent_color: '#32C574'
    text_color: '#111111'
    h1_color: '#652e8e'
    h2_color: '#652e8e'
monitoring:
  enabled: true
cdsdashboards:
  enabled: true
  cds_hide_user_named_servers: true
  cds_hide_user_dashboard_servers: false
ci_cd:
  type: github-actions
  branch: main
terraform_state:
  type: remote
namespace: dev
local:
  kube_context: arn:aws:eks:<region>:xxxxxxxxxxxx:cluster/<existing_cluster_name>
  node_selectors:
    general:
      key: eks.amazonaws.com/nodegroup
      value: general
    user:
      key: eks.amazonaws.com/nodegroup
      value: user
    worker:
      key: eks.amazonaws.com/nodegroup
      value: worker
profiles:
  jupyterlab:
  - display_name: Small Instance
    description: Stable environment with 2 cpu / 8 GB ram
    default: true
    kubespawner_override:
      cpu_limit: 2
      cpu_guarantee: 1.5
      mem_limit: 8G
      mem_guarantee: 5G
      image: quansight/qhub-jupyterlab:v0.3.13
  - display_name: Medium Instance
    description: Stable environment with 4 cpu / 16 GB ram
    kubespawner_override:
      cpu_limit: 4
      cpu_guarantee: 3
      mem_limit: 16G
      mem_guarantee: 10G
      image: quansight/qhub-jupyterlab:v0.3.13
  dask_worker:
    Small Worker:
      worker_cores_limit: 2
      worker_cores: 1.5
      worker_memory_limit: 8G
      worker_memory: 5G
      worker_threads: 2
      image: quansight/qhub-dask-worker:v0.3.13
    Medium Worker:
      worker_cores_limit: 4
      worker_cores: 3
      worker_memory_limit: 16G
      worker_memory: 10G
      worker_threads: 4
      image: quansight/qhub-dask-worker:v0.3.13
environments:
  environment-dask.yaml:
    name: dask
    channels:
    - conda-forge
    dependencies:
    - python
    - ipykernel
    - ipywidgets
    - qhub-dask ==0.3.13
    - python-graphviz
    - numpy
    - numba
    - pandas
  environment-dashboard.yaml:
    name: dashboard
    channels:
    - conda-forge
    dependencies:
    - python==3.9.7
    - ipykernel==6.4.1
    - ipywidgets==7.6.5
    - qhub-dask==0.3.13
    - param==1.11.1
    - python-graphviz==0.17
    - matplotlib==3.4.3
    - panel==0.12.7
    - voila==0.2.16
    - streamlit==1.0.0
    - dash==2.0.0
    - cdsdashboards-singleuser==0.5.7

```

</details>

Once updated, deploy QHub. When prompted be ready to manually update the DNS record.

- `local` or "existing" deployments fail if you pass `--dns-auto-provision` or `--disable-prompt`

```
python -m qhub deploy --config qhub-config.yaml
```

The deployment completes successfully and all the pods appear to be running and so do the pre-existing Guestbook web
app.
