# Troubleshooting

Invariably you will encounter behavior that does not match your expectations. This guide is meant to explain that behavior, help you diagnose it, and if possible resolve it.

[_Behavior_](#behavior)

 - DNS domain=1your_nebari_domain1 record does not exist

[_Errors_](#errors)
 
 - Conda-Store environment fails to build

[_How do I...?_](#how-do-i)

 - Get kubernetes context
 - Debug your kubernetes cluster

## Behavior

### DNS domain=`your_nebari_domain` record does not exist

During your initial Nebari deployment, at the end of the `04-kubernetes-ingress` stage, you may receive an output message stating that the DNS record for `your_qhub_domain` "appears not to exist, has recently been updated, or has yet to fully propagate."

As the output message mentions, this is likely the result of the non-deterministic behavior of DNS.

Without going into a deep dive of what DNS is or how it works, the issue encountered here is that when Nebari tries to look up the IP address associated with the DNS record, `your_qhub_domain`, nothing is returned. Unfortunately, this "lookup" is not as straightforward as it sounds. To lookup the correct IP associated with this domain, many intermediate servers (root, top level domain, and authoritative nameservers) are checked, each with their own cache, and each cache has its own update schedule (usually on the order of minutes, but not always).

(If you are so inclined to learn more about DNS, [see this interesting comic](https://howdns.works/))

As the output message mentions, it will ask if you want it to retry this DNS lookup again after another wait period; this wait period keeps increasing after each retry. However, it's possible that after waiting 15 or more minutes that the DNS still won't resolve.

At this point, feel free to cancel the deployment and rerun the same deployment command again in an hour or two. Although not guaranteed, it's extremely likely that the DNS will resolve correctly after this prolonged wait period.

## Errors

### Conda-Store environment fails to build

One of the two Conda-Store environments created during the initial Nebari deployment (`dashboard` or `dask`) may fail to appear as options when logged into JupyterHub.

If your user has access to Conda-Store, you can verify this by visiting `<your_qhub_domain>.com/conda-store` and having a look at the build status of the missing environment.

The reason for this issue is due to how these environments are simultaneously built. Under the hood, Conda-Store relies on Mamba/Conda to resolve and download the specific packages listed in the environment YAML. If both environment builds try to download the same package with different versions, the build that started first will have their package overwritten by the second build. This causes the first build to fail.

To resolve this issue, navigate to `<your_qhub_domain>.com/conda-store`, find the environment build that failed and trigger it to re-build.

## How do I...?

### Get kubernetes context

Depending on a variety of factors, `kubectl` may not be able to access your Kubernetes cluster. To configure this utility for access, depending on your cloud provider:

#### [Digital Ocean](https://www.digitalocean.com/docs/kubernetes/how-to/connect-to-cluster/)
1. [Download the Digital Ocean command line utility](https://www.digitalocean.com/docs/apis-clis/doctl/how-to/install/).
2. If you haven't already, create a [Digital Ocean API token](https://www.digitalocean.com/docs/apis-clis/doctl/how-to/install/).
3. [Authenticate via the API token](https://www.digitalocean.com/docs/apis-clis/doctl/how-to/install/): `doctl auth init`
4. Run the following command: `doctl kubernetes cluster kubeconfig save "<project-name>-<namespace>"`

#### [Google Cloud Platform](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl)
1. Download the [GCP SDK](https://cloud.google.com/sdk/downloads).
2. Authenticate with GCP: `gcloud init`
3. Run the following command: `gcloud container clusters get-credentials <project-name>-<namespace> --region <region>`

#### [Amazon Web Services](https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html)
1. Download the [AWS CLI](https://aws.amazon.com/cli/).
2. If you haven't already, [create an AWS Access Key and Secret Key](https://aws.amazon.com/premiumsupport/knowledge-center/create-access-key/).
3. Run the following command: `aws eks --region <region-code> update-kubeconfig --name <project-name>-<namespace>`

After completing these steps according to your cloud provider, `kubectl` should be able to access your Kubernetes cluster.

### Debug your Kubernetes Cluster

If you need more information about your Kubernetes cluster, [`k9s`](https://k9scli.io/) is a terminal-based UI that is extremely useful for debugging. It simplifies navigating, observing, and managing your applications in Kubernetes. `k9s` continuously monitors Kubernetes clusters for changes and provides shortcut commands to interact with the observed resources. It's a fast way to review and resolve day-to-day issues in Kubernetes, a huge improvement to the general workflow, and a best-to-have tool for debugging your Kubernetes cluster sessions.

[Installation instructions for macOS, Windows, and Linux](https://github.com/derailed/k9s) are available.

By default, `k9s` starts with the standard directory that's set as the context (in this case Minikube). To view all the current process press 0:

![Image of the k9s terminal UI](../static/images/k9s_UI.png)

> **NOTE**: In some circumstances, you will be confronted with the need to inspect any services launched by your cluster at your `localhost`. For instance, if your cluster has problem with the network traffic tunnel configuration, it may limit or block the user’s access to destination resources over the connection.

`k9s` port-forward option <kbd>shift</kbd> + <kbd>f</kbd> allows you to access and interact with internal Kubernetes cluster processes from your localhost you can then use this method to investigate issues and adjust your services locally without the need to expose them beforehand.