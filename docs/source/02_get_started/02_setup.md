# Setup Initialization

QHub Cloud offers two usage options: 
+ [Local](../06_developers_contrib_guide/04_tests#local-testing) deployment, used for testing.
+ [Cloud](#cloud-deployment) deployment for all else (_default_).

We advise users with existing Kubernetes clusters to start with local deployment to test the clusters, since local 
testing is significantly easier to perform than testing clusters on the Cloud. On the other hand, if you are starting 
  from scratch i.e., you have no clusters yet, try the Cloud option.

## Local Deployment
The local version is recommended for testing QHub's components due to its simplicity. It is important to highlight that 
while it is possible to test most of QHub with this version, components which are Cloud provisioned such as, 
VPCs, managed Kubernetes cluster, and managed container registries cannot be locally tested due to their Cloud dependencies.

For more information on how to set up Local deployment, follow the [Tests section](../06_developers_contrib_guide/04_tests#local-testing)
on the Developers documentation.


## Cloud Deployment
The Cloud version of QHub requires a choice of [Cloud provider](#cloud-provider), 
[authentication (using Auth0 and GitHub)](#authentication), [domain registration](#domain-registry), and GitHub Actions tokens.

These services will generate global [environment variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/)
that once set up will trigger QHub's automatic deploy using GitHub Actions.

To find and set the environment variables, follow the steps described on the subsections below.

### Cloud Provider
The first required step is to **choose a Cloud Provider to host the project deployment**. The cloud installation is based
on Kubernetes, but knowledge of Kubernetes is **NOT** required. QHub supports [Amazon AWS](#amazon-web-services-(aws)), 
[DigitalOcean](#digital-ocean), [GCP](#google-cloud-platform), and [Azure](#microsoft-azure).

To deploy QHub, all access keys require fairly wide permissions. Hence, once the Cloud provider has been chosen, follow 
the steps below and set the environment variables as specified with owner/admin level permissions.


For more details on configuration for each Cloud provider, check the How-To Guides section of the documentation.

#### Amazon Web Services (AWS)

Please see these instructions for [creating an IAM role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html)
with admin permissions and set the following variables:
```bash
export AWS_ACCESS_KEY_ID      #the public access key for an IAM account
export AWS_SECRET_ACCESS_KEY  #the Private key for an IAM account
export AWS_DEFAULT_REGION     #the region where you intend to deploy QHub
```

#### Digital Ocean

In order to get the DigitalOcean access keys follow the steps below:

- `DIGITALOCEAN_TOKEN`: Follow [these instructions](https://www.digitalocean.com/docs/apis-clis/api/create-personal-access-token/)
  to create a Personal Access token.
- `SPACES_ACCESS_KEY_ID`: Follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key)
  to create a Spaces access key.
- `SPACES_SECRET_ACCESS_KEY`: The secret acquired from the step above. 
- `AWS_ACCESS_KEY_ID`: Due to a Terraform quirk, set this variable to be the same as `SPACES_ACCESS_KEY_ID`.
- `AWS_SECRET_ACCESS_KEY`: Again, due to the quirk, set this variable the same as `SPACES_SECRET_ACCESS_KEY`.

#### Google Cloud Platform

Follow [these detailed instructions](https://cloud.google.com/iam/docs/creating-managing-service-accounts) to create a 
Google Service Account with Owner level permissions. Then, follow the steps described on the  
[GCP docs](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-console)
to create and download a JSON credentials file.

- `GOOGLE_CREDENTIALS`: Set this to the path to your credentials file.
- `PROJECT_ID`: Set this to the `project-id` listed on the home page of your Google console, under `Project info`.

#### Microsoft Azure
Follow [these instructions](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_client_secret#creating-a-service-principal-in-the-azure-portal) 
to create a Service Principal in the Azure Portal. After completing the 3 steps described on the link, set the 
environment variables below by running the following commands:
```bash
export ARM_CLIENT_ID="00000000-0000-0000-0000-000000000000"       # application (client) ID
export ARM_CLIENT_SECRET="00000000-0000-0000-0000-000000000000"   # client's secret
export ARM_SUBSCRIPTION_ID="00000000-0000-0000-0000-000000000000" # subscription ID (Available at the Subscription section under the **Overview** tab)
export ARM_TENANT_ID="00000000-0000-0000-0000-000000000000"       # directory (tenant) ID
```

#### Local (Existing) Kubernetes Cluster

To deploy on an existing kubernetes cluster kubectl must be setup and
have the cluster available as one of the kubectl contexts. In the
`qhub-config.yaml` you can specify a non-default context name
`local.kube_context` but is not required since it will use the default
(current) context.

```shell
kubectl config get-contexts
```

### Authentication
#### Auth0
To create the necessary access tokens you will need to have an [Auth0](https://auth0.com/) account and be logged in.
- Click on the `Applications` button on the left
- Select `Create Application` > `Machine to Machine Applications` > `Auth0 Management API` from the dropdown menu
- Next, click `All` next to `Select all` and click `Authorize`
  - Set the variable `AUTH0_CLIENT_ID` equal to the `Cliend ID` string, and do the same for the `Client secret` by running the command below.
  
```shell
export AUTH0_CLIENT_ID="secretClientID"
export AUTH0_CLIENT_SECRET="verylongstringofcharactersthatrepresentthesecretkey"
```
Finally, set the `AUTH0_DOMAIN` variable to your account name (indicated on the upper righthand corner) appended with 
`.auth0.com`, for example:
```shell
export AUTH_DOMAIN="qhub-test.auth0.com" # in case the account was called 'qhub-test'
```

#### GitHub 
QHub uses GitHub Actions to trigger the CI/CD checks on the configuration file that automatically generates
the Terraform modules for the deployment infrastructure. To do that, it will be necessary to set the GitHub username and
token as environment variables.
```shell
export GITHUB_USERNAME="quansight"
export GITHUB_TOKEN="GitHubAccessTokenGenerated"
```
### Domain registry
Finally, you will need to have a domain name for hosting QHub. This domain will be where your application will be exposed.

Currently, QHub only supports CloudFlare for automatic DNS registration. If an alternate DNS provider is desired, 
change the `--dns-provider` flag from `cloudflare` to `none` on the `qhub deploy` command. The deployment then will be 
paused when it asks for an IP address (or CNAME, if using AWS) and prompt to register the desired URL.

#### CloudFlare
If using Cloudflare, first create a Cloudflare account and register your application domain name on it.

To generate a token:
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
```shell
export CLOUDFLARE_TOKEN="cloudflaretokenforthisapplication"

```

You are now done with the hardest part of the deployment.

On the next section, you will generate the main configuration file and render the Terraform modules to generate the
deployment infrastructure.
