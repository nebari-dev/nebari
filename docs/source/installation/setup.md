# Setup Initialization

QHub handles the initial setup and management of configurable data
science environments, allowing users to attain seamless deployment
with Github Actions or GitLab Workflows.

QHub will be deployed on a cloud of your choice (AWS, Google Cloud, Azure, or Digital Ocean), first preparing requisite cloud infrastructure including a Kubernetes cluster.

It is suitable for most use cases, especially when:
- You require scalable infrastructure
- You aim to have a production environment with administration managed via simple configuration stored in git

QHub requires a choice of [Cloud
provider](#cloud-provider), [authentication (using Auth0, GitHub, or
password based)](#authentication), [domain
registration](#domain-registry), and CI provider (GitHub Actions).

These services require global [environment
variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/)
that once set up will trigger QHub's automatic deploy using GitHub
Actions.

To find and set the environment variables, follow the steps described
in the subsections below.

> NOTE: **Other QHub approaches**
>
> It is possible to deploy QHub into an existing Kubernetes cluster (on a cloud or otherwise), or into a local Kubernetes simulation on your personal computer (for testing). See [Testing](../dev_guide/testing.md).
>
> [QHub HPC](https://hpc.qhub.dev/) is a different codebase to regular QHub, aiming for a similar data science platform, and should be your choice if
> - You have highly optimized code that requires highly performant infrastructure
> - You have existing HPC infrastructure already available
> - You expect that your infrastructure will **not** exceed the existing resources capabilities

## Cloud Provider

The first required step is to **choose a Cloud Provider to host the
project deployment**. The cloud installation will be within a new Kubernetes cluster,
but knowledge of Kubernetes is **NOT** required nor is in depth
knowledge about the specific provider required either. QHub supports
[Amazon AWS](#amazon-web-services-aws),
[DigitalOcean](#digital-ocean), [GCP](#google-cloud-platform), and
[Azure](#microsoft-azure).

To deploy QHub, all access keys require fairly wide permissions to
create all the resources. Hence, once the Cloud provider has been
chosen, follow the steps below and set the environment variables as
specified with **owner/admin** level permissions.

You will need to tell `qhub init` which cloud provider you have chosen, in the [Usage](usage.md) section, and this must correspond with the environment variables set for your chosen cloud as below:

### Amazon Web Services (AWS)
<details><summary>Click for AWS configuration instructions </summary>

Please see these instructions for [creating an IAM
role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html)
with administrator permissions. Upon generation, the IAM role will provide a public **access
key ID** and a **secret key** which will need to be added to the environment variables.

To define the environment variables paste the commands below with your respective keys.

```bash
export AWS_ACCESS_KEY_ID="HAKUNAMATATA"
export AWS_SECRET_ACCESS_KEY="iNtheJUng1etheMightyJUNgleTHEl10N51eEpsT0n1ghy;"
```
</details>

#### Digital Ocean
<details><summary>Click to expand DigitalOcean configuration directions </summary>

Please see these instructions for [creating a Digital Ocean
token](https://www.digitalocean.com/docs/apis-clis/api/create-personal-access-token/). In
addition to a `token`, `spaces key` (similar to AWS S3) credentials are also required. Follow the instructions on the
[official docs](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key) for more information.
> Note: DigitalOcean's permissions model is not as fine-grained as the other supported Cloud providers.

Set the required environment variables as specified below:

```bash
export DIGITALOCEAN_TOKEN=""          # API token required to generate resources
export SPACES_ACCESS_KEY_ID=""        # public access key for access spaces
export SPACES_SECRET_ACCESS_KEY=""    # the private key for access spaces
export AWS_ACCESS_KEY_ID=""           # set this variable with the same value as `SPACES_ACCESS_KEY_ID`
export AWS_SECRET_ACCESS_KEY=""       # set this variable identical to `SPACES_SECRET_ACCESS_KEY`
```
</details>

### Google Cloud Platform

<details><summary>Click for CGP configuration specs </summary>

Follow [these detailed instructions](https://cloud.google.com/iam/docs/creating-managing-service-accounts) to create a
Google Service Account with **owner level** permissions. Then, follow the steps described on the official
[GCP docs](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-console)
to create and download a JSON credentials file. Store this credentials file in a well known location and make sure to
set yourself exclusive permissions.

You can change the file permissions by running the command `chmod 600 <filename>` on your terminal.

In this case the environment variables will be such as follows:
```bash
export GOOGLE_CREDENTIALS="path/to/JSON/file/with/credentials"
export PROJECT_ID="projectIDName"
```
> NOTE: the [`PROJECT_ID` variable](https://cloud.google.com/resource-manager/docs/creating-managing-projects) can be
> found at the Google Console homepage, under `Project info`.
</details>

### Microsoft Azure

<details><summary>Click for Azure configuration details </summary>

Follow [these instructions](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_client_secret#creating-a-service-principal-in-the-azure-portal)
to create a Service Principal in the Azure Portal. After completing the steps described on the link, set the following environment variables such as below:
```bash
export ARM_CLIENT_ID=""           # application (client) ID
export ARM_CLIENT_SECRET=""       # client's secret
export ARM_SUBSCRIPTION_ID=""     # value available at the `Subscription` section under the `Overview` tab
export ARM_TENANT_ID=""           # field available under `Azure Active Directories` > `Properties` > `Tenant ID`
```
> NOTE 1: Having trouble finding your Subscription ID? [Azure's official docs](https://docs.microsoft.com/en-us/azure/media-services/latest/how-to-set-azure-subscription?tabs=portal)
> might help.

> NOTE 2: [Tenant ID](https://docs.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-how-to-find-tenant)
> values can be also found using PowerShell and CLI.
</details>

## Authentication

User identity in QHub is now managed within Keycloak which is a robust and highly flexible open source identity and access management solution. A Keycloak instance will be deployed inside your QHub.

It can be configured to work with many OAuth2 identity providers, it can federate users from existing databases (such as LDAP), or it can be used as a simple database of username/passwords.

The full extent of possible configuration can't be covered here, so we provide three simple options that can be configured automatically by QHub when it sets up your new platform. These options are basic passwords, GitHub single-sign on, or Auth0 single-sign on (which in turn can be configured to allow identity to be provided by social login etc).

You will actually instruct `qhub init` which method you have chosen when you move on to the [Usage](usage.md) section, but at this stage you may need to set environment variables corresponding to your choice:

### Auth0

<details><summary>Click for Auth0 configuration details </summary>
Auth0 is a great choice to enable flexible authentication via multiple
providers. To create the necessary access tokens you will need to have
an [Auth0](https://auth0.com/) account and be logged in. [Directions
for creating an Auth0
application](https://auth0.com/docs/applications/set-up-an-application/register-machine-to-machine-applications).

- Click on the `Applications` button on the left
- Select `Create Application` > `Machine to Machine Applications` > `Auth0 Management API` from the dropdown menu
- Next, click `All` next to `Select all` and click `Authorize`
- Set the variable `AUTH0_CLIENT_ID` equal to the `Cliend ID` string, and do the same for the `Client secret` by running the command below.

The following environment variables must be set:

 - `AUTH0_CLIENT_ID`: client ID of Auth0 machine-to-machine application
 - `AUTH0_CLIENT_SECRET`: secret ID of Auth0 machine-to-machine application
 - `AUTH0_DOMAIN`: Finally, set the `AUTH0_DOMAIN` variable to your account name (indicated on the upper right-hand
   corner) appended with `.auth0.com`, for example:

```bash
export AUTH_DOMAIN="qhub-test.auth0.com" # in case the account was called 'qhub-test'
```
</details>

### GitHub Single-sign on

<details><summary>Click for GitHub SSO configuration details </summary>
To use GitHub as a single-sign on provider, you will need to provide env vars for a new OAuth2 app.

TODO
</details>

## CI/CD Pipeline

In the [Usage](usage.md) section, you will need to run `qhub init` (this only ever needs to be run once - it creates your configuration YAML file) and then `qhub deploy` to set up the cloud infrastructure and deploy QHub for the first time.

For subsequent deployments, it is possible to run `qhub deploy` again in exactly the same way, providing the configuration YAML file as you would the first time. However, it is also possible to automate future deployments using 'DevOps' - the configuration YAML file stored in git will trigger automatic redeployment whenever it is edited.

This DevOps approach can be provided by GitHub Actions or GitLab Workflows. As for the other choices, you will only need to specify the CI/CD provider when you come to run `qhub init`, but you may need to set relevant environment variables unless you choose 'none' because you plan to always redeploy manually.

### GitHub

<details><summary>Click for GitHub Actions configuration details </summary>
QHub uses GitHub Actions to enable [Infrastructure as
Code](https://en.wikipedia.org/wiki/Infrastructure_as_code) and
trigger the CI/CD checks on the configuration file that automatically
generates the deployment modules for the infrastructure. To
do that, it will be necessary to set the GitHub username and token as
environment variables. First create a github personal access token via
[these
instructions](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token). The
token needs permissions to create a repo and create secrets on the
repo. At the moment we don't have the permissions well scoped out so
to be on the safe side enable all permissions.

 - `GITHUB_USERNAME`: your GitHub username
 - `GITHUB_TOKEN`: token generated by GitHub
</details>

### GitLab

<details><summary>Click for GitLab Workflow configuration details </summary>
TODO
</details>

## Domain registry

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

### Cloudflare

<details><summary>Click for Cloudflare configuration details </summary>
QHub supports Cloudflare as a DNS provider. If you choose to use Cloudflare, first
create an account, then there are two possible following options:
1. You can either register your application domain name on it, using the [Cloudflare
nameserver](https://support.cloudflare.com/hc/en-us/articles/205195708-Changing-your-domain-nameservers-to-Cloudflare)
(recommended), or
2. You can outright buy a new domain with Cloudflare (this action is not particularly recommended).

To generate a token [follow these steps](https://developers.cloudflare.com/api/tokens/create):

- Under `Profile`, select the `API Tokens` menu and click on `Create API Token`.
- On `Edit zone DNS` click on `Use Template`.
![screenshot Cloudflare edit Zone DNS](../images/cloudflare_auth_1.png)
- Configure `Permissions` such as the image below:
![screenshot Cloudflare Permissions edit](../images/cloudflare_permissions_2.1.1.png)
- On `Account Resources` set the configuration to include your desired account
![screenshot Cloudflare account resources](../images/cloudflare_account_resources_scr.png)
- On `Zone Resources` set it to `Include | Specific zone` and your domain name
![screenshot Cloudflare account resources](../images/cloudflare_zone_resources.png)
- Click continue to summary
![screenshot Cloudflare summary](../images/cloudflare_summary.png)
- Click on the `Create Token` button and set the token generated as an environment variable on your machine.

Finally, set the environment variable such as:
```bash
 export CLOUDFLARE_TOKEN="cloudflaretokenvalue"
```

</details>

----

You are now done with the hardest part of the deployment.

In the next section, you will create the main configuration YAML file and then deploy the QHub infrastructure.
