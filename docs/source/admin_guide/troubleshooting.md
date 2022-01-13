# Troubleshooting and further setup

This guide aims to provide useful information to developers in the detection and correction of issues within QHub.

## General Troubleshooting

To minimize the occurrence of errors on your QHub application, please follow the best practices described on the [Installation](../installation/installation.md), [Setup](../installation/setup.md) and [Usage](../installation/usage.md) sections.

### Solutions for common problems

#### Getting Kubernetes Context

##### Digital Ocean

To get the kubernetes context to interact with a Digital Ocean cluster use the [following instructions](https://www.digitalocean.com/docs/kubernetes/how-to/connect-to-cluster/).

1. [Download Digital Ocean command line utility](https://www.digitalocean.com/docs/apis-clis/doctl/how-to/install/)
2. [Create Digital Ocean API Token](https://www.digitalocean.com/docs/apis-clis/doctl/how-to/install/) likely already done
3. [doctl access via api token](https://www.digitalocean.com/docs/apis-clis/doctl/how-to/install/) `doctl auth init`
4. `doctl kubernetes cluster kubeconfig save "<project-name>-<namespace>"`

After completing these steps. `kubectl` should be able to access the cluster.

##### Google Cloud Platform

To get the kubernetes context to interact with a GCP use the [following instructions](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl).

1. [Download the GCP SDK](https://cloud.google.com/sdk/downloads)
2. Login to GCP via `gcloud init`
3. `gcloud container clusters get-credentials <project-name>-<namespace> --region <region>`

After completing these steps. `kubectl` should be able to access the cluster.

##### Amazon Web Services

To get the kubernetes context to interact with a AWS use the [following instructions](https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html).

1. Download the [aws command line](https://aws.amazon.com/cli/)
2. [Create AWS Access Key and Secret Key](https://aws.amazon.com/premiumsupport/knowledge-center/create-access-key/) likely already done
2. `aws eks --region <region-code> update-kubeconfig --name <project-name>-<namespace>`

After completing these steps. `kubectl` should be able to access the cluster.

#### Debug your Kubernetes cluster

[`k9s`](https://k9scli.io/) is a terminal-based UI to manage Kubernetes clusters that aims to simplify navigating, observing, and managing your applications in `k8s`. `k9s` continuously monitors Kubernetes clusters for changes and provides shortcut commands to interact with the observed resources becoming a fast way to review and resolve day-to-day issues in Kubernetes. It's definitely a huge improvement to the general workflow, and a best-to-have tool for debugging your Kubernetes cluster sessions.

Installation can be done on macOS, Windows, and Linux. Instructions for each operating system can be found [here](https://github.com/derailed/k9s). Complete the installation to follow along.

By default, `k9s` starts with the standard directory that's set as the context (in this case Minikube). To view all the current process press `0`:

![Image of the `k9s` terminal UI](../images/k9s_UI.png)

> **NOTE**: In some circumstances you will be confronted with the need to inspect any services launched by your cluster at your ‘localhost’. For instance, if your cluster has problem
with the network traffic tunnel configuration, it may limit or block the user's access to destination resources over the connection.

`k9s` port-forward option <kbd>shift</kbd> + <kbd>f</kbd> allows you to access and interact with internal Kubernetes cluster processes from your localhost you can then use this method to investigate issues and adjust your services locally without the need to expose them beforehand.

---

## Further Setup

### Theming

#### JupyterHub Theme

The QHub theme was originally based off the [work of the pangeo team](https://github.com/pangeo-data/pangeo-custom-jupyterhub-templates) and is now located in [github.com/Quansight/qhub-jupyterhub-theme](https://github.com/Quansight/qhub-jupyterhub-theme/). For simple modifications to the jupyterhub theme we suggest only editing `infrastructure/jupyterhub.yaml` and the value `c.JupyterHub.template_vars`. For most use cases this should provide enough flexibility.

```yaml
hub:
  extraConfig:
    customPodHook: |
      c.JupyterHub.template_paths = ['/usr/local/share/jupyterhub/custom_templates/']
      c.JupyterHub.template_vars = {
          'pangeo_hub_title': 'QHub - $do-jupyterhub',
          'pangeo_hub_subtitle': 'Autoscaling Compute Environment on Digital Ocean',
          'pangeo_welcome': """Welcome to $. It is maintained by the <a href="http://quansight.com">Quansight staff</a>. The hub's configuration is stored in the github repository based on <a href="https://github.com/Quansight/qhub-kubernetes/">https://github.com/Quansight/qhub-kubernetes/</a>. To provide feedback and report any technical problems, please use the <a href="https://github.com/Quansight/qhub-kubernetes//issues">github issue tracker</a>."""
      }
```

For more serious modifications to the jupyterhub theme you will need to fork [Quansight/qhub-jupyterhub-theme](https://github.com/Quansight/qhub-jupyterhub-theme) and edit the jupyterhub Dockerfile located at `image/Dockerfile.jupyterhub`. Modify the `THEME_OWNER`, `THEME_REPO`, and `THEME_REV`. This should change the Dockerfile to use your new theme. The [Quansight/qhub-jupyterhub-theme](https://github.com/Quansight/qhub-jupyterhub-theme) has detailed documentation.

#### JupyterLab Theme

Setting the JupyterLab theme is done via extensions. Edit the `image/postBuild` script to include the jupyterlab extension in the build. Within the `image` directory run the following to build JupyterLab.

```shell
docker build -f Docker.jupyterlab -t Quansight/qhub-jupyterlab:latest .
```

Finally, you can test the resulting image via the following docker command and open your web browser to `localhost:8000`.

```shell
docker run -p 8000:8000 -it Quansight/qhub-jupyterlab:latest jupyter lab --port 8000 --ip 0.0.0.0
```

### Using a Private AWS ECR Container Registry

By default, images such as the default JupyterLab image specified as `quansight/qhub-jupyterhub:v||QHUB_VERSION||` will be pulled from Docker Hub.

To specify a private AWS ECR (and this technique should work regardless of which cloud your QHub is deployed to), first provide details of the ECR and AWS access keys in `qhub-config.yaml`:

```yaml
external_container_reg:
  enabled: true
  access_key_id: <AWS access key id>
  secret_access_key: <AWS secret key>
  extcr_account: 12345678
  extcr_region: us-west-1
```

This will mean you can specify private Docker images such as `12345678.dkr.ecr.us-west-1.amazonaws.com/quansight/qhub-jupyterlab:mytag` in your `qhub-config.yaml` file. The AWS key and secret provided must have relevant ecr IAMS permissions to authenticate and read from the ECR container registry.
