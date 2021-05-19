# Step-by-Step QHub Deployment

The list below is our suggestion. Other providers may be used, but you
will need to consult their documentation. When using a different
provider the corresponding flag in the `qhub` command-line argument
should be omitted.

For this initial tutorial, we assume that you will use the following
tools:

- [Github Actions](https://github.com/features/actions) will be used for CI/CD
- Oauth will be via [Auth0](https://auth0.com/)
- DNS registry will be through [Cloudflare](https://www.cloudflare.com/)

## 1. Install QHub
Following best practice, we recommend that you create a virtual
environment previously and from there install QHub on machine:

- If you prefer conda, install the latest stable release with :

```bash
    conda install -c conda-forge qhub
```

- If you are a PyPI user instead, download the latest stable release with:
```bash
    pip install qhub
```

- (For developers) The latest development version can be installed using PyPI:
```bash
    pip install git+https://github.com/Quansight/qhub.git
```
> NOTE: Download the 'development version' to try out features which have not been yet officially released.


## 2. Environment variables

The purpose of all these environment variables is that one gets to use APIs to deploy QHub.
In order to fully automate the deployment, several environment variables must be set. The following subsections will
describe the purpose and method for obtaining the values for these variables. An introduction to unix environment variables can be found [here](https://en.wikipedia.org/wiki/Environment_variable).

### 2.1 Domain Name Server Registry

Cloudflare will handle the automation of the DNS registration. First, a [Cloudflare][Cloudflare_signup] account needs to be created and
[domain name] registered through it. If an alternate DNS provider is desired, then omit the `--dns-provider cloudflare`
flag for `qhub deploy`. At the end of deployment an IP address (or CNAME for AWS) will be output that can be registered
to your desired URL.

Within your Cloudflare account, follow these steps to generate a token

- Click user icon on top right and click `My Profile`
- Click the `API Tokens` menu and select `Create Token`
- Click `Use Template` next to `Edit zone DNS`
- Under `Permissions` in addition to `Zone | DNS | Edit` use the `Add more` button to add `Zone | Zone | Read`, `Zone |
  Zone Settings | Read`, and `Account | Account Settings | Read` to the Permissions
- Under `Account Resources` set the first box to `Include` and the second to your desired account
- Under `Zone Resources` set it to `Include | Specific zone` and your domain name
- Click continue to summary
- Click Create Token
- To set your environment variable to you new token. On your terminal type:
    ```bash
  export CLOUDFLARE_TOKEN='token_generated'
    ```
  > For more information on environment variables, check out [this blogpost](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/).

### 2.2 Auth0

After creating an [Auth0](https://auth0.com/) account and logging in, follow these steps to create a access token:

- Click Applications on the left
- Click `Create Application`
- Select `Machine to Machine Applications`
- Select `Auth0 Management API` from the dropdown
- Click `All` next to `Select all` and click `Authorize`
- `AUTH0_CLIENT_ID`: Set this variable equal to the `Cliend ID` string under `Settings`
- `AUTH0_CLIENT_SECRET`: Set this variable equal to the `Client Secret` string under `Settings`
- `AUTH0_DOMAIN`: Set this variable to be equal to your account name (indicated on the upper right) appended with `.auth0.com`. IE an account called `qhub-test` would have this variable set to `qhub-test.auth0.com`

### 2.3 GitHub
Your GitHub username and access token will automate the creation of the repository that will hold the infrastructure code as well as the github secrets

- `GITHUB_USERNAME`: Set this to your GitHub username
- `GITHUB_TOKEN`: Set this equal to your [github access token]


### 2.4 Cloud Provider Credentials
To deploy QHub, the access key for the Cloud providers will require fairly wide permissions.

As such, all testing for QHUb has been done with owner/admin level permissions.
We welcome testing to determine the minimum required permissions for deployment [(open issue)](https://github.com/Quansight/qhub/issues/173).

#### 2.4.1 Amazon Web Services

Please see these instructions for [creating an IAM role] with admin permissions and set the below variables.

- `AWS_ACCESS_KEY_ID`: The public key for an IAM account
- `AWS_SECRET_ACCESS_KEY`: The Private key for an IAM account

#### 2.4.2 Digital Ocean

In order to get the DigitalOcean access keys follow this [digitalocean tutorial].

- `DIGITALOCEAN_TOKEN`: Follow [these instructions] to create a digital ocean token
- `SPACES_ACCESS_KEY_ID`: Follow [this guide] to create a spaces access key/secret
- `SPACES_SECRET_ACCESS_KEY`: The secret from the above instructions
- `AWS_ACCESS_KEY_ID`: Due to a [terraform] quirk, set to the same as `SPACES_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`: Due to the quirk, set to the same as `SPACES_SECRET_ACCESS_KEY`

#### 2.4.3 Google Cloud Platform

Follow [these detailed instructions] on creating a Google service account with an owner level permissions. With the service account created, follow [these steps] to create and download a json credentials file.

- `GOOGLE_CREDENTIALS`: Set this to the path to your credentials file
- `PROJECT_ID`: Set this to the project ID listed on the home page of your Google console under `Project info`

#### 2.4.3 Azure
Follow [these instructions](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_client_secret#creating-a-service-principal-in-the-azure-portal) to create a Service Principal in Azure Portal (Stop after completing steps 1-3).  Set the following environment variables as you go through the instructions.

- `ARM_CLIENT_ID`: Application (client) ID
- `ARM_CLIENT_SECRET`: Client Secret
- `ARM_SUBSCRIPTION_ID`: Subscription ID (Available on Overview tab of Subscription)
- `ARM_TENANT_ID`: Directory (tenant) ID

We're done with the hardest part of deployment!

### 2.5 QHub init

The next step is to run `qhub init` to generate the configuration file `qhub-config.yaml`. This file is where the vast majority of tweaks to the system will be made. There are are several optional (yet highly recommended) flags that deal with automating the deployment:

- `--project`: Chose a name consisting of lowercase letters and numbers only and is between 3 and 16 characters long. IE `testcluster`
- `--domain`: This is the base domain for your cluster. After deployment, the DNS will use the base name prepended with `jupyter`. IE if the base name is `test.qhub.dev` then the DNS will be provisioned as `jupyter.test.qhub.dev`. This pattern is also applicable if you are setting your own DNS through a different provider.
- `--ci-provider`: This specifies what provider to use for ci-cd. Currently, github-actions is supported.
- `--auth-provider`: This will set configuration file to use auth0 for authentication
- `--auth-auto-provision`: This will automatically create and configure an auth0 application
- `--repository`: The repository name that will be used to store the infrastructure as code
- `--repository-auto-provision`: This sets the secrets for the github repository

Best practices is to create a new directory and run all the qhub commands inside of it. An example of the full command is below:

`qhub init gcp --project test-project --domain test.qhub.dev --ci-provider github-actions --auth-provider auth0 --auth-auto-provision --repository github.com/quansight/qhub-test --repository-auto-provision`

### 2.6 QHub deploy

Finally, we can deploy with:

    qhub deploy -c qhub-config.yaml --dns-provider cloudflare --dns-auto-provision

You will notice that several directories are created:
  - `environments` : conda environments are stored
  - `infrastructure` : Terraform files that declare state of infrastructure
  - `terraform-state` : required by Terraform to securely store the state of the Terraform deployment
  - `image` : docker images used in QHub deployment including: jupyterhub, jupyterlab, and dask-gateway

The terminal will prompt to press `[enter]` to check oauth credentials (which were added by qhub init). After pressing `enter` the deployment will continue and take roughly 10 minutes. Part of the output will show an "ip" address (DO/GCP) or a CNAME "hostname" (AWS) based on the the cloud service provider:

    Digital Ocean/Google Cloud Platform:

        Outputs:

        ingress_jupyter = {
        "hostname" = ""
        "ip" = "xxx.xxx.xxx.xxx"
        }

    AWS:
        Outputs:

        ingress_jupyter = {
        "hostname" = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxx.us-east-1.elb.amazonaws.com"
        "ip" = ""
        }


### 2.7 Push repository

Add all files to github:

    git add .github/ .gitignore README.md environments/ image/ infrastructure/ qhub-config.yaml  terraform-state/

Push the changes to your repo:

    git push origin main


## 3. Post GitHub deployment:

After the files are in Github all CI/CD changes will be triggered by a commit to main and deployed via GitHub actions. To use gitops, make a change to `qhub-config.yaml` in a new branch and create a pull request into main. When the pull request is merged, it will trigger a deployment of all of those changes to your QHub.

The first thing you will want to do is add users to your new QHub. Any type of supported authorization from auth0 can be used as a username. Below is an example configuration of 2 users:

        joeuser@example:
            uid: 1000000
            primary_group: users
            secondary_groups:
                - billing
                - admin
        janeuser@example.com:
            uid: 1000001
            primary_group: users

As seen above, each username has a unique `uid` and a `primary_group`.
Optional `secondary_groups` may also be set for each user.

## 4. GitOps enabled

Since the infrastructure state is reflected in the repository, it allows self-documenting of infrastructure and team
members to submit pull requests that can be reviewed before modifying the infrastructure.

Congratulations! You have now completed your QHub cloud deployment!

[Github actions]: https://github.com/features/actions
[via github]: https://docs.github.com/en/free-pro-team@latest/developers/apps/authorizing-oauth-apps
[auth0]: https://auth0.com/
[Cloudflare]: https://www.cloudflare.com/
[AWS Environment Variables]: https://github.com/Quansight/qhub/blob/ft-docs/docs/docs/aws/installation.md
[Digital Ocean Environment Variables]: https://github.com/Quansight/qhub/blob/ft-docs/docs/docs/do/installation.md
[Google Cloud Platform]: https://github.com/Quansight/qhub/blob/ft-docs/docs/docs/gcp/installation.md
[Cloudflare_signup]: https://dash.cloudflare.com/sign-up
[domain name]: https://www.cloudflare.com/products/registrar/
[github_oath]: https://developer.github.com/apps/building-oauth-apps/creating-an-oauth-app/
[doctl]: https://www.digitalocean.com/docs/apis-clis/doctl/how-to/install/
[oauth application]: https://docs.github.com/en/free-pro-team@latest/developers/apps/authorizing-oauth-apps
[recording your DNS]: https://support.cloudflare.com/hc/en-us/articles/360019093151-Managing-DNS-records-in-Cloudflare
[github access token]: https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token
[creating an IAM role]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html
[digitalocean tutorial]: https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key
[these instructions]: https://www.digitalocean.com/docs/apis-clis/api/create-personal-access-token/
[this guide]: https://www.digitalocean.com/community/tutorials/how-to-create-a-digitalocean-space-and-api-key
[terraform]: https://www.terraform.io/
[these detailed instructions]: https://cloud.google.com/iam/docs/creating-managing-service-accounts
[these steps]: https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-console
[is a compliant name for S3/Storage buckets]: https://www.google.com/search?q=s3+compliant+name&oq=s3+compliant+name&aqs=chrome..69i57j0.3611j0j7&sourceid=chrome&ie=UTF-8
