# Usage

## Cloud Deployment

Great, you've gone through the `qhub` [Installation](installation.md) and [Setup Initialization](setup.md) steps, and have ensured that all the necessary environment variables have
been properly set, it is time to deploy QHub from your terminal.

### Initialize configuration

There are several ways to generate your configuration file. You can type the commands when prompted by terminal, or you can set it all automatically from the start. In any case, we
advise you to start by creating a new project folder. Here, we will name the new folder `qhub-test`.

On your terminal run:

```shell
mkdir qhub-test && cd qhub-test
```

#### Fully automated deployment

To generate a fully automated configuration file, on your terminal run:

```shell
qhub init aws \
  --project projectname --domain mysite.com \
  --ci-provider github-actions \
  --repository github.com/quansight/project-name --repository-auto-provision  \
  --auth-provider auth0 --auth-auto-provision \
  --ssl-cert-email admin@test.com
```

There are several **optional** (yet highly recommended) flags that allow to configure the deployment:

The command above will generate the `qhub-config.yaml` config file with an infrastructure deployed on `aws`, named `projectname`, where the domain will be `qhub.dev`.

The deployment will use `github-actions` as the continuous integration (CI) provider, automatically provisioning a repository on GitHub under the URL
`github.com/quansight/projectname`

User authentication will be by `auth0`, and an OAuth 2.0 app will be created on Auth0 automatically. There are several flags that allow you to configure the deployment:

- `aws` indicates that the project will be deployed on the Amazon AWS Cloud provider.
  - Optional flags are: `gcp`, `do` and `azure`.
- `--project`: the name of the project is required to be a string compliant with the Cloud provider recommendations. For more details see official Cloud provider docs on naming
  policies and see below on the [project naming convention](#project-naming-convention).
- `--domain`: base domain for your cluster. This pattern is also applicable if you are setting your own DNS through a different provider.
  - `qhub.dev` is the domain registered on CloudFlare. If you chose not to use Cloudflare, skip this flag.
- `--ci-provider`: specifies what provider to use for CI/CD. Currently, supports GitHub Actions, GitLab CI, or none.
- `--auth-provider`: This will set configuration file to use the specified provider for authentication.
- `--auth-auto-provision`: This will automatically create and configure an application using OAuth.
- `--repository`: Repository name that will be used to store the Infrastructure-as-Code on GitHub.
- `--repository-auto-provision`: Sets the secrets for the GitHub repository used for CI/CD actions.
- `--ssl-cert-email`: Provide an admin's email address so that LetsEncrypt can generate a real SSL certificate for your site. If omitted, the site will use a self-signed cert that
  may cause problems for some browsers but may be sufficient for testing.

You will be prompted to enter values for some of the choices above if they are omitted as command line arguments (for example project name and domain).

The `qhub init` command also generates an initial password for your root Keycloak user:

```
Securely generated default random password=R1E8aWedaQVU6kKv for Keycloak root user stored at path=/tmp/QHUB_DEFAULT_PASSWORD
```

This password is also available in the `qhub-config.yaml` file under the `security.keycloak.initial_root_password field`. It's required in the next page of these docs for logging
in to your QHub.

This `qhub init` command generates the `qhub-config.yaml` config file with an infrastructure to be deployed on `aws`, named `projectname`, with a domain name set to `qhub.dev`. The
deployment uses `github-actions` as the continuous integration provider, automatically provisioned and authenticated by `auth0`. And finally, initialized on GitHub under the URL
`github.com/quansight/projectname`.

If employing an infrastructure-as-code approach, this is where you would make the desired infrastructure changes including adding users, changing Dask worker instance type and much
more. Once you're happy with your changes you would redeploy those changes using GitHub Actions. For more details on the `qhub-config.yaml` please see
[Configuration](configuration.md)

The proceeding command will generate the `qhub-config.yaml` config file with an infrastructure deployed on `aws`, named `projectname`, where the domain will be `qhub.dev`. The
deployment will use `github-actions` as the continuous integration (CI) provider, automatically provisioned and authenticated by `auth0`, initialized on GitHub under the URL
`github.com/quansight/projectname`.

If employing an infrastructure-as-code approach, this is where you would make the desired infrastructure changes including adding environments, changing Dask worker instance type
and much more. Once you're happy with your changes you would redeploy those changes using GitHub Actions. For more details on the `qhub-config.yaml` please see
[Configuration](configuration.md)

##### Project Naming Convention

In order to successfully deploy QHub, there are some project naming conventions which need to be followed. For starters, make sure your project name is compatible with the
specifics of your chosen Cloud provider. In addition, QHub `projectname` should also obey to the following format requirements:

> - letters from A to Z (upper and lower case) and numbers;
> - Special characters are **NOT** allowed;
> - Maximum accepted length of the name string is 16 characters.
> - If using AWS names **SHOULD NOT** start with the string `aws`

### Understanding the qhub-config.yaml file

The `qhub init` command may have some side-effects such automatically creating a GitHub repository and setting some repo secrets (if you used the `--repository-auto-provision`
flag), and creating an Auth0 app, but the main output of the command is the `qhub-config.yaml` file.

This file is the configuration file that will determine how the cloud infrastructure and QHub is built and deployed in the next step. But at this point it's just a text file. You
could edit it manually if you are unhappy with the choices, or delete it and start over again. It is also possible to create this config file from scratch or re-use an existing
one. Ulimately it's not essential to use `qhub init` at all, but it's often the easiest way to get started.

To understand some ways in which you could decide to edit the YAML file, see [Advanced Configuration](configuration.md).

## Deploy QHub

Finally, with the `qhub-config.yaml` created, QHub can be deployed for the first time:

```shell
qhub deploy -c qhub-config.yaml --dns-provider cloudflare --dns-auto-provision
```

> Omit `--dns-provider cloudflare --dns-auto-provision` if you are not using Cloudflare and will set up your DNS manually.

This creates the following folder structure:

```
.
├── .github             # if "--ci-provider github-actions" was passed in, then an action scripts folder is also generated
├── environments        # stores the conda environments
├── image               # docker images used on deployment: jupyterhub, jupyterlab, and dask-gateway
│   ├── dask-worker
│   ├── jupyterlab
│   └── scripts
├── infrastructure      # contains Terraform files that declare state of infrastructure
└── terraform-state     # required by terraform to securely store the state of the deployment
```

The terminal will prompt you to press `[enter]` to check auth credentials (which were added by the `qhub init` command). That will trigger the deployment which will take around 10
minutes to complete.

During the initial deployment, Digital Ocean, GCP and Azure are going to display an `"ip"` address whereas AWS is going to display a CNAME `"hostname"`.

- Digital Ocean/Google Cloud Platform

```shell
    ingress_jupyter = {
            "hostname" = ""
            "ip" = "xxx.xxx.xxx.xxx"
            }
```

- AWS:

```shell
    ingress_jupyter = {
    "hostname" = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxx.us-east-1.elb.amazonaws.com"
    "ip" = ""
    }
```

If you specified `--dns-provider cloudflare --dns-auto-provision` on the command line, your DNS records for your domain should be updated automatically on Cloudflare. If you
omitted those flags, you will be prompted to set the A/CNAME records manually on your domain name registrar's nameservers.

### GitOps

If you chose `--ci-provider github-actions` (or `gitlab-ci`) then QHub will use a GitHub Actions workflow (or GitLab equivalent) to automatically handle future deployment of the
infrastructure. For that to work, your newly generated project must be pushed to GitHub. Using the URL under the `--repository` flag on the `qhub init` command, you need to commit
all files to the git repo.

To add the project to the initialized remote git repository run:

```shell
git add .github/ .gitignore environments/ image/ infrastructure/ qhub-config.yaml terraform-state/
git commit -m "First commit"
```

Push the changes to the repository (your primary branch may be called `master` instead of `main`):

```shell
git push origin main
```

Once the files are in GitHub, all CI/CD changes will be triggered by commits to main, and deployed via GitHub Actions. Since the infrastructure state is reflected in the
repository, this workflow allows for team members to submit pull requests that can be reviewed before modifying the infrastructure, easing the maintenance process.

To automatically deploy (and to keep track of changes more effectively):

- make changes to the `qhub-config.yaml` file on a new branch.
- create a pull request (PR) to main.
- Trigger the deployment by merging the PR. All changes will be automatically applied to the new QHub instance.

Having issues? Head over to our [Troubleshooting](../admin_guide/troubleshooting.md) section for tips on how to debug your QHub. Or try our [FAQ](../admin_guide/faq.md).

If your deployment seemed to be successful, next learn how to [login](login.md).
