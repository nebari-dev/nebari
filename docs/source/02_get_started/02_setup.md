# Setup Initialization

QHub Cloud offers several usage options: 
+ [Local](../06_developers_contrib_guide/04_tests.md#local-testing) deployment, used for testing.
+ [Cloud](#cloud-deployment) deployment for all else (_default_).

We advise users with existing Kubernetes clusters to start with local
deployment to test the clusters, since local testing is significantly
easier to perform than testing clusters on the Cloud. On the other
hand, if you are starting from scratch i.e., you have no clusters yet,
try the Cloud option.

## Local Deployment

The local version is recommended for testing QHub's components due to
its simplicity and deploying on existing kubernetes clusters. It is
important to highlight that while it is possible to test most of QHub
with this version, components which are Cloud provisioned such as,
VPCs, managed Kubernetes cluster, and managed container registries
cannot be locally tested due to their Cloud dependencies.

For more information on how to set up Local deployment, follow the
[Tests section](../06_developers_contrib_guide/04_tests#local-testing)
on the Developers documentation.

## Cloud Deployment

The Cloud version of QHub requires a choice of [Cloud
provider](#cloud-provider), [authentication (using Auth0, GitHub, or
password based)](#authentication), [domain
registration](#domain-registry), and [ci provider (GitHub Actions)]().

These services require global [environment
variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/)
that once set up will trigger QHub's automatic deploy using GitHub
Actions.

To find and set the environment variables, follow the steps described
on the subsections below.

### Cloud Provider

The first required step is to **choose a Cloud Provider to host the
project deployment**. The cloud installation is based on Kubernetes,
but knowledge of Kubernetes is **NOT** required nor is in depth
knowledge about the specific provider required either. QHub supports
[Amazon AWS](#amazon-web-services-aws),
[DigitalOcean](#digital-ocean), [GCP](#google-cloud-platform), and
[Azure](#microsoft-azure).

To deploy QHub, all access keys require fairly wide permissions to
create all the resources. Hence, once the Cloud provider has been
chosen, follow the steps below and set the environment variables as
specified with owner/admin level permissions.

For more details on configuration for each Cloud provider, check the
How-To Guides section of the documentation.

#### Amazon Web Services (AWS)

Please see these instructions for [creating an IAM
role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html)
with admin permissions. This IAM role should provide you the access
key and secret key. Additionally the [AWS
region](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
needs to be set. Have the following environment variables defined:

 - `AWS_ACCESS_KEY_ID`: the public access key for an IAM account
 - `AWS_SECRET_ACCESS_KEY`: the private key for an IAM account
 - `AWS_DEFAULT_REGION`: the region where you intend to deploy QHub

#### Digital Ocean

Please see these instructions for [creating a Digital Ocean
token](https://www.digitalocean.com/docs/apis-clis/api/create-personal-access-token/). In
addition to a `token` a spaces (similar to AWS S3) credentials are
required [follow these
intructions](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key). Note
that digital ocean's permissions model is not as fine grained as other
providers such as AWS, GCP, and Azure. Set the following environment
variables in your environment:

- `DIGITALOCEAN_TOKEN`: API token required to generate resources
- `SPACES_ACCESS_KEY_ID`: the public access key for access spaces
- `SPACES_SECRET_ACCESS_KEY`: the private key for access spaces
- `AWS_ACCESS_KEY_ID`: Due to a Terraform quirk, set this variable to be the same as `SPACES_ACCESS_KEY_ID`.
- `AWS_SECRET_ACCESS_KEY`: Again, due to the quirk, set this variable the same as `SPACES_SECRET_ACCESS_KEY`.

#### Google Cloud Platform

Follow [these detailed instructions](https://cloud.google.com/iam/docs/creating-managing-service-accounts) to create a 
Google Service Account with Owner level permissions. Then, follow the steps described on the  
[GCP docs](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-console)
to create and download a JSON credentials file. Store this credentials file in a well known location and make sure to set the permissions so only you have access `chmod 600 <filename>`.

- `GOOGLE_CREDENTIALS`: Set this to the path to your credentials file.
- `PROJECT_ID`: Set this to the [`project-id`](https://cloud.google.com/resource-manager/docs/creating-managing-projects) listed on the home page of your Google console, under `Project info`.

#### Microsoft Azure

Follow [these instructions](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_client_secret#creating-a-service-principal-in-the-azure-portal) 
to create a Service Principal in the Azure Portal. After completing the 3 steps described on the link, set the following environment variables:

 - `ARM_CLIENT_ID`: application (client) ID
 - `ARM_CLIENT_SECRET`: client's secret
 - `ARM_SUBSCRIPTION_ID`: [Subscription ID](https://docs.microsoft.com/en-us/azure/media-services/latest/how-to-set-azure-subscription?tabs=portal) (Available at the Subscription section under the **Overview** tab)
 - `ARM_TENANT_ID`: [Tenant ID](https://docs.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-how-to-find-tenant)

#### Local (Existing) Kubernetes Cluster

To deploy on an existing kubernetes cluster kubectl must be setup and
have the cluster available as one of the kubectl contexts. In the
`qhub-config.yaml` you can specify a non-default context name
`local.kube_context` but is not required since it will use the default
(current) context.

```bash
kubectl config get-contexts
```

### Authentication

#### Auth0

Auth0 is a great choice to enable flexible authentication via multiple
providers. To create the necessary access tokens you will need to have
an [Auth0](https://auth0.com/) account and be logged in. [Directions
for creating an Auth0
application](https://auth0.com/docs/applications/set-up-an-application/register-machine-to-machine-applications).

- Click on the `Applications` button on the left
- Select `Create Application` > `Machine to Machine Applications` > `Auth0 Management API` from the dropdown menu
- Next, click `All` next to `Select all` and click `Authorize`
- Set the variable `AUTH0_CLIENT_ID` equal to the `Cliend ID` string, and do the same for the `Client secret` by running the command below.

The following environment variables must be set
  
 - `AUTH0_CLIENT_ID`: client id of Auth0 machine-to-machine application
 - `AUTH0_CLIENT_SECRET`: secret id of Auth0 machine-to-machine application
 - `AUTH0_DOMAIN`: Finally, set the `AUTH0_DOMAIN` variable to your account name (indicated on the upper righthand corner) appended with `.auth0.com`, for example:

```shell
export AUTH_DOMAIN="qhub-test.auth0.com" # in case the account was called 'qhub-test'
```

#### GitHub 

QHub uses GitHub Actions to enable [Infrastructure as
Code](https://en.wikipedia.org/wiki/Infrastructure_as_code) and
trigger the CI/CD checks on the configuration file that automatically
generates the Terraform modules for the deployment infrastructure. To
do that, it will be necessary to set the GitHub username and token as
environment variables. First create a github personal access token via
[these
instructions](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token). The
token needs permissions to create a repo and create secrets on the
repo. At the moment we don't have the permissions well scoped out so
to be on the safe side enable all permissions.

 - `GITHUB_USERNAME`: your GitHub username
 - `GITHUB_TOKEN`: token that GitHub generated

### Domain registry

Finally, you will need to have a domain name for hosting QHub. This
domain will be where your application will be exposed.

Currently, QHub only supports CloudFlare for automatic DNS
registration. If an alternate DNS provider is desired, change the
`--dns-provider` flag from `cloudflare` to `none` on the `qhub deploy`
command. The deployment then will be paused when it asks for an IP
address (or CNAME, if using AWS) and prompt to register the desired
URL. Setting a DNS record heavily depends on the provider thus it is
not possible to have detailed docs on how to create a record on your
provider. Googling `setting <A/CNAME> record on <provider name>`
should yield good results on doing it for your specific provider.

#### CloudFlare

Qhub supports cloudflare as a DNS provider. If using Cloudflare, first
create a Cloudflare account and either register your application
domain name on it, use the [cloudflare
nameserver](https://support.cloudflare.com/hc/en-us/articles/205195708-Changing-your-domain-nameservers-to-Cloudflare)
**recommended**, or outright buy a new domain with Cloudflare (not
recommended).

To generate a token [do the following steps](https://developers.cloudflare.com/api/tokens/create):

- Under `Profile`, select the `API Tokens` menu and click on `Create API Token`.
- On `Edit zone DNS` click on `Use Template`.
![screenshot Cloudflare edit Zone DNS](../meta_images/cloudflare_auth_1.png)
- Configure `Permissions` such as the image below:
![screenshot Cloudflare Permissions edit](../meta_images/cloudflare_permissions_2.1.1.png)
- On `Account Resources` set the configuration to include your desired account
![screenshot Cloudflare account resources](../meta_images/cloudflare_account_resources_scr.png)  
- On `Zone Resources` set it to `Include | Specific zone` and your domain name
![screenshot Cloudflare account resources](../meta_images/cloudflare_zone_resources.png)
- Click continue to summary
![screenshot Cloudflare summary](../meta_images/cloudflare_summary.png)  
- Click on the `Create Token` button and set the token generated as an environment variable on your machine.

Finally set the environment variable:

 - `CLOUDFLARE_TOKEN`: CloudFlare api token

You are now done with the hardest part of the deployment.

On the next section, you will generate the main configuration file and
render the Terraform modules to generate the deployment
infrastructure.
