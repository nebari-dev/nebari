# Installation

[Terraform installation directions](https://www.terraform.io/downloads.html).

The following steps can be automated with
`scripts/00-guided-install.sh`. When the script prompts the user for
pressing `[enter]` there is an associated user action required.

## Environment Variables

This deployment along with the GitHub Actions assumes several
environment variables are present. 

{% if cookiecutter.ci_cd == 'github-actions' %}
Since we are using Github Actions for Continuous Deployment we require
a [personal api token](https://github.blog/2013-05-16-personal-api-tokens/). 
This token is required to have access to the **full repo** and **workflows**. 
Set `REPOSITORY_ACCESS_TOKEN` to the token value. This token is required because
as of github actions v2 `GITHUB_TOKEN` cannot trigger github actions.

 - `REPOSITORY_ACCESS_TOKEN`
{% endif %}

{% if cookiecutter.provider == 'aws' %}
 - `AWS_ACCESS_KEY_ID`
 - `AWS_SECRET_ACCESS_KEY`
 - `AWS_DEFAULT_REGION`

Note that the AWS IAM user must have extensive permissions since the
role will be creating eks, s3, ecr, iam, and vpc resources.  

{% elif cookiecutter.provider == 'do' %} 

In order to get the DigitalOcean access keys follow this [digitalocean
tutorial](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key).

 - `AWS_ACCESS_KEY_ID`
 - `AWS_SECRET_ACCESS_KEY`
 - `SPACES_ACCESS_KEY_ID`
 - `SPACES_SECRET_ACCESS_KEY`
 - `DIGITALOCEAN_TOKEN`

Note that the reason we require an AWS and SPACES environment
variable is due to limitations in Terraform. `AWS_ACCESS_KEY_ID` is
the same as your `SPACES_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` is
the same as your `SPACES_SECRET_ACCESS_KEY`.

Since the DigitalOcean [container
registry](https://www.digitalocean.com/products/container-registry/)
is not general availability yet and the Terraform [PR for support is
not merged](https://github.com/terraform-providers/terraform-provider-digitalocean/pull/383) we require an external container registry. The simplest one to choose is Docker hub. Thus for DigitalOcean we also require Docker Hub access tokens ([tutorial](https://docs.docker.com/docker-hub/access-tokens/)).

 - `DOCKER_USERNAME`
 - `DOCKER_PASSWORD`

{% elif cookiecutter.provider == 'gcp' %}

Google Cloud deployment requires the project id and service account
credentials.

 - `GOOGLE_CREDENTIALS`
 - `PROJECT_ID`
 
`GOOGLE_CREDENTIALS` must be the contents of the `json` credentials
file with sufficient permissions to create all resources on the
cluster. Detailed instructions on [creating service accounts can be
found
here](https://cloud.google.com/iam/docs/creating-managing-service-account-keys). `PROJECT_ID`
is a short string of around 32 characters that defines your project
uniquely. The service account will need `Project->Editor`
permissions. In addition you will need to enable the `Cloud Resource
Manager API`. The deployment will fail without the api enabled.

{% endif %}

## Bootstrapping

Terraform is used for all deployments of infrastructure as well as
Kubernetes state. In order to use Infrastructure as code with
repositories we need somewhere to store the terraform state in between
invocations. The default is to store the state in the local git
repository which is not ideal for several reasons including checking
in secrets to the repository. Each provider has a different best way
to deploy the infrastructure.

{% if cookiecutter.provider == 'aws' %}

The most common remote backend is using
an AWS S3 bucket with DynamoDB. S3 is used to store the terraform json
state file while DynamoDB is used to lock the terraform update process
so that the infrastructure/cluster can only be update in a serial
fashion.

The [terraform-state](../terraform-state) directory deploys this
infrastructure. Currency this bucket is named
`crowdsmart-terraform-state` with the DynamoDB table named
`crowdsmart-terraform-state-lock`. A single remote backend can be used
for many terraform deployments.

{% elif cookiecutter.provider == 'do' %}

{% elif cookiecutter.provider == 'gcp' %}

Google Cloud storage provides an s3 compatible storage with additional
benefits such as built in file locking.

{% endif %}

Finally to bootstrap run the following commands

```shell
cd terraform-state
terraform init
terraform apply # reply yes
```

## Kubernetes Installation

Once the setup has been bootstrapped we recommend letting GitHub
actions take over from this point on. This means setting the
environment variables mentioned above as secrets. One additional
benefit of this approach. Is that After bootstrapping the terraform
state no one needs to have access to the credentials (only github
actions). If you would like to perform the installation locally we
follow the same terraform deployment steps.

```shell
cd infrastructure
terraform init
terraform apply -target=module.kubernetes -target=module.kubernetes-initialization -target=module.kubernetes-ingress # reply yes
```

Notice a pattern here with terraform deployments? `terraform init` +
`terraform apply` should be enough to maintain the entire
cluster. About 15 minutes after these commands or the GitHub Action
starting you will have a working jupyterhub cluster.

## Checking the Cluster via CLI

* Install the AWS CLI:
https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

* Update the kubeconfig:

```bash
aws eks --region us-west-2  update-kubeconfig --name jupyterhub-aws-dev
```

Now you can run `kubectl` and `helm` commands to know about your cluster and deployments.
Here are some useful commands:

```bash
kubectl get pods -n dev
kubectl get nodes -n dev
helm list -n dev
```

# DNS

The DNS is handled by Cloudflare. To point the cloudflare subdomain
`jupyter.aws`(.qhub.dev) to your application, first get the CNAME of
the Load balancer. You can get the CNAME of the load balancer via the
following command:

```bash
kubectl get svc -n dev
```
This lists all the running services in the Kubernetes cluster. There would be a service
of type `LoadBalancer`, listed in the output of the above command. The CNAME would
be mentioned right next to it.

Now go to the DNS section of the Cloudflare's dashboard and create an `CNAME` record for the
subdomain `jupyter.aws`(.qhub.dev) and paste the CNAME of the load balancer in the content
column and click on the proxy status to change the value to DNS only.

# Authentication

Currently the authentication is being performed by Github OAuth. Instructions to come on.

# QHub Installation

```shell
cd infrastructure
terraform init
terraform apply # reply yes
```
