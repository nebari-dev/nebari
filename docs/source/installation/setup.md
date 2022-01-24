# Setup Initialization

QHub handles the initial setup and management of configurable data
science environments, allowing users to deploy seamlessly
using Github Actions.

QHub can be installed on a bare-metal server using HPC, on a Cloud
provider or even locally for testing purposes. Review the options
below to discover which option best suits your needs.

## Local Deployment or Existing Kubernetes Cluster

The local version is recommended for testing QHub's components due to
its simplicity. Choose the local mode if:

- You already have Kubernetes clusters
- You want to test these Kubernetes clusters
- You have available local compute setup
- You want to try out QHub with a quick-install to see how it works,
  without setting up environment variables

You should choose another installation option if you are starting from
scratch (i.e., no clusters yet) and aiming to have a production
environment.

Found your match? Head over to the [Local install
docs](../dev_guide/testing.md#local-testing) for
more details.

## HPC Deployment

The [QHub HPC](https://hpc.qhub.dev/en/latest/) should be your choice if:
- You have highly optimized code that require highly performant infrastructure
- You have existing infrastructure already available
- You expect that your infrastructure will **not** exceed the existing resources capabilities
> NOTE: Although it is possible to deploy QHub HPC on the Cloud, it is not generally recommended due to possible high
> costs. For more information, check out the [base cost](../admin_guide/cost.md) section of the docs.

## Kubernetes Deployment

The Kubernetes deployment of QHub is considered to be the default
option. If you are not sure which option to choose, try this one. It
is suitable for most use cases, especially if:
- You require scalable infrastructure
- You aim to have a production environment with GitOps enabled by default

The QHub version requires a choice of [Cloud
provider](#cloud-provider), [authentication (using Auth0, GitHub, custom OAuth provider, or
password based)](#authentication), [domain
registration](#domain-registry), and CI provider (GitHub Actions, GitLab CI).

These services require global [environment
variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/)
that once set up, will trigger QHub's automatic deploy using your
CI/CD platform of choice.

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
create all the necessary cloud resources. Hence, once the Cloud
provider has been chosen, follow the steps below and set the
environment variables as specified with **owner/admin** level
permissions.

For more details on configuration for each Cloud provider, check the
How-To Guides section of the documentation.

#### Amazon Web Services (AWS)
<details><summary>Click for AWS configuration instructions </summary>

Please see these instructions for [creating an IAM role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html) with administrator permissions. Upon generation, the IAM role will provide a public **access
key ID** and a **secret key** which will need to be added to the environment variables.

To define the environment variables paste the commands below with your respective keys.

```shell
export AWS_ACCESS_KEY_ID="HAKUNAMATATA"
export AWS_SECRET_ACCESS_KEY="iNtheJUng1etheMightyJUNgleTHEl10N51eEpsT0n1ghy;"
```
</details>

### Digital Ocean

<details><summary>Click to expand DigitalOcean configuration directions </summary>

Please see these instructions for [creating a Digital Ocean token](https://www.digitalocean.com/docs/apis-clis/api/create-personal-access-token/). In addition to a `token`, a `spaces key` (similar to AWS S3) credentials are also required. Follow the instructions on the [official docs](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key) for more information.

> Note: DigitalOcean's permissions model isn't as fine-grained as the other supported Cloud providers.

Set the required environment variables as specified below:

```shell
export DIGITALOCEAN_TOKEN=""          # API token required to generate resources
export SPACES_ACCESS_KEY_ID=""        # public access key for access spaces
export SPACES_SECRET_ACCESS_KEY=""    # the private key for access spaces
export AWS_ACCESS_KEY_ID=""           # set this variable with the same value as `SPACES_ACCESS_KEY_ID`
export AWS_SECRET_ACCESS_KEY=""       # set this variable identical to `SPACES_SECRET_ACCESS_KEY`
```
</details>

### Google Cloud Platform

<details><summary>Click for CGP configuration specs </summary>

Follow [these detailed instructions](https://cloud.google.com/iam/docs/creating-managing-service-accounts) to create a Google Service Account with **owner level** permissions. Then, follow the steps described on the official
[GCP docs](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-console) to create and download a JSON credentials file. Store this credentials file in a well known location and make sure to set yourself exclusive permissions.

You can change the file permissions by running the command `chmod 600 <filename>` on your terminal.

In this case the environment variables will be such as follows:

```shell
export GOOGLE_CREDENTIALS="path/to/JSON/file/with/credentials"
export PROJECT_ID="projectIDName"
```

> NOTE: the [`PROJECT_ID` variable](https://cloud.google.com/resource-manager/docs/creating-managing-projects) can be
> found at the Google Console homepage, under `Project info`.
</details>

### Microsoft Azure

<details><summary>Click for Azure configuration details </summary>

Follow [these instructions](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_client_secret#creating-a-service-principal-in-the-azure-portal) to create a Service Principal in the Azure Portal. After completing the steps described on the link, set the following environment variables such as below:

```shell
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

User identity in QHub is now managed within Keycloak which is a robust and highly flexible open source identity and access management solution. A Keycloak instance will be deployed inside your QHub. It can be configured to work with many OAuth 2.0 identity providers, it can federate users from existing databases (such as LDAP), or it can be used as a simple database of username/passwords.

The full extent of possible configuration can't be covered here, so we provide three simple options that can be configured automatically by QHub when it sets up your new platform. These options are basic passwords, GitHub single-sign on, or Auth0 single-sign on (which in turn can be configured to allow identity to be provided by social login etc).

You will actually instruct `qhub init` which method you have chosen when you move on to the [Usage](usage.md) section, but at this stage you may need to set environment variables corresponding to your choice:

### Auth0

<details><summary>Click for Auth0 configuration details </summary>

Auth0 is a great choice to enable flexible authentication via multiple providers. To create the necessary access tokens you will need to have an [Auth0](https://auth0.com/) account and be logged in. [Directions
for creating an Auth0 application](https://auth0.com/docs/applications/set-up-an-application/register-machine-to-machine-applications).

- Click on the `Applications` button on the left
- Select `Create Application` > `Machine to Machine Applications` > `Auth0 Management API` from the dropdown menu
- Next, click `All` next to `Select all` and click `Authorize`
- Set the variable `AUTH0_CLIENT_ID` equal to the `Client ID` string, and do the same for the `Client secret` by running the command below.

With the application created set the following environment variables:

 - `AUTH0_CLIENT_ID`: client ID of Auth0 machine-to-machine application found at top of the newly created application page
 - `AUTH0_CLIENT_SECRET`: secret ID of Auth0 machine-to-machine application found in the `Settings` tab of the newly created application
 - `AUTH0_DOMAIN`: The `Tenant Name` which can be found in the general account settings on the left hand side of the page appended with `.auth0.com`, for example:

```bash
export AUTH_DOMAIN="qhub-test.auth0.com" # in case the Tenant Name was called 'qhub-test'
```
</details>

### GitHub Single-sign on

<details><summary>Click for GitHub SSO configuration details </summary>

To use GitHub as a single-sign on provider, you will need to create a new OAuth 2.0 app.

No environment variables are needed for this - you will be given the relevant information and prompted for various inputs during the next stage, when you run [`qhub init`](./usage.md) if you provide the flag `--auth-provider github`. This will be covered when you reach that point in this documentation.
</details>

## CI/CD Pipeline

In the [Usage](usage.md) section, you will need to run `qhub init` (this only ever needs to be run once - it creates your configuration YAML file) and then `qhub deploy` to set up the cloud infrastructure and deploy QHub for the first time.

For subsequent deployments, it's possible to run `qhub deploy` again in exactly the same way, providing the configuration YAML file as you would the first time. However, it's also possible to automate future deployments using 'DevOps' - the configuration YAML file stored in git will trigger automatic redeployment whenever it's edited.

This DevOps approach can be provided by GitHub Actions or GitLab Workflows. As for the other choices, you will only need to specify the CI/CD provider when you come to run `qhub init`, but you may need to set relevant environment variables unless you choose 'none' because you plan to always redeploy manually.

### GitHub

<details><summary>Click for GitHub Actions configuration details </summary>

QHub uses GitHub Actions to enable [Infrastructure as Code](https://en.wikipedia.org/wiki/Infrastructure_as_code) and trigger the CI/CD checks on the configuration file that automatically generates the deployment modules for the infrastructure. To do that, it will be necessary to set the GitHub username and token as environment variables. First create a github personal access token via [these instructions](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token). The token needs permissions to create a repo and create secrets on the repo. At the moment we don't have the permissions well scoped out so to be on the safe side enable all permissions.

 - `GITHUB_USERNAME`: GitHub username
 - `GITHUB_TOKEN`: GitHub-generated token
</details>

### GitLab

<details><summary>Click for GitLab Workflow configuration details </summary>

If you want to use GitLab CI to automatically deploy changes to your configuration, then no extra environment variables are needed for this.

All git repo and CI setup on GitLab will need to be done manually. At the next stage, when you run [`qhub init`](./usage.md) please provide the flag `--ci-provider gitlab-ci`.

After initial deploy, the documentation should tell you when to commit your configuration files into your GitLab repo. There should be your `qhub-config.yaml` file as well as a generated file called `.gitlab-ci.yml`. You will need to manually set environment variables for your cloud provider as secrets in your GitLab CI for the repo.
</details>

## Domain registry

Finally, you will need to have a domain name for hosting QHub. This domain will be where your application will be exposed.

Currently, QHub only supports CloudFlare for automatic DNS registration. If an alternate DNS provider is desired, change the `--dns-provider` flag from `cloudflare` to `none` on the `qhub deploy` command. The deployment then will be paused when it asks for an IP address (or CNAME, if using AWS) and prompt to register the desired URL. Setting a DNS record heavily depends on the provider thus it's not possible to have detailed docs on how to create a record on your provider. Googling `setting <A/CNAME> record on <provider name>` should yield good results on doing it for your specific provider.

### Cloudflare

<details><summary>Click for Cloudflare configuration details </summary>

QHub supports Cloudflare as a DNS provider. If you choose to use Cloudflare, first create an account, then there are two possible following options:

1. You can register your application domain name on it, using the [Cloudflare nameserver](https://support.cloudflare.com/hc/en-us/articles/205195708-Changing-your-domain-nameservers-to-Cloudflare)
(recommended).
2. You can outright buy a new domain with Cloudflare (this action isn't particularly recommended).

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

```shell
 export CLOUDFLARE_TOKEN="cloudflaretokenvalue"
```

</details>

----

You are now done with the hardest part of the deployment.

In the next section, you will create the main configuration YAML file and then deploy the QHub infrastructure.
