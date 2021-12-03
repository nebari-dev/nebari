# Usage

## Cloud Deployment

Once all environment variables have been set (in [Configuration](configuration.md)), you will be able to run
commands on your terminal to initialise the configuration for QHub, and then deploy it.

### Initialize configuration

QHub can help you create your configuration YAML file, and you can further edit it as needed.

We advise you to
start by creating a new project folder. Here, we will name the new
folder `qhub-test`.

On your terminal run:

```shell
mkdir qhub-test && cd qhub-test
```

To generate a configuration file, on your terminal run something like the following (vary for your own choices):

```shell
qhub init aws \
  --project projectname --domain mysite.com \
  --ci-provider github-actions \
  --repository github.com/quansight/project-name --repository-auto-provision  \
  --auth-provider auth0 --auth-auto-provision \
  --ssl-cert-email admin@test.com
```

The command above will generate the `qhub-config.yaml` config file
with an infrastructure deployed on `aws`, named `projectname`, where
the domain will be `qhub.dev`.

The deployment
will use `github-actions` as the continuous integration (CI) provider,
automatically provisioning a repository on GitHub under the URL `github.com/quansight/projectname`

User authentication will be by `auth0`, and an OAuth2 app will be created on Auth0 automatically.

There are several flags that allow you to configure the deployment:

- `aws` indicates that the project will be deployed on the Amazon AWS Cloud provider.
    + Other providers are: `gcp`, `do` and `azure`.
- `--project`: the name of the project is required to be a string compliant with the Cloud provider recommendations. For
  more details see official Cloud provider docs on naming policies and check the [note below](#project-naming-convention).
- `--domain`: domain for your cluster. This pattern is also required if you are setting your own DNS through a provider other than Cloudflare.
- `--ci-provider`: specifies what provider to use for CI/CD. Currently, supports GitHub Actions, GitLab CI, or none ("github-actions", "gitlab-ci", or "none").
- `--auth-provider`: This will set configuration file to use the specified provider for user authentication (value can be "auth0", "github", or "password").
- `--auth-auto-provision`: This will automatically create and configure an application using OAuth (assuming `--auth-provider` is `auth0` or `github`).
- `--repository`: Repository name that will be used to store the Infrastructure-as-Code on GitHub.
- `--repository-auto-provision`: Sets the secrets for the GitHub repository used for CI/CD actions.
- `--ssl-cert-email`: Provide an admin's email address so that LetsEncrypt can generate a real SSL certificate for your site. If omitted, the site will use a self-signed cert that may cause problems for some browsers but may be sufficient for testing.
- `--shared-users-group`: If provided, will ensure a `users` group is created and all users will become members. This means a shared folder called `users` will be available to share files with all other users.
- `--disable-prompt`: Don't wait to ask for inputs for missing flags and values.

You will be prompted to enter values for some of the choices above if they are omitted as command line arguments (e.g. project name and domain, and whether to create a shared users group or not). If you supply the `--disable-prompt` then you will not be asked for inputs - defaults will be used, or the text PLACEHOLDER used in the resulting `qhub-config.yaml` file so you supply necessary values before deploying.

The `qhub init` command will also generate an initial password for your root Keycloak user:

```
Securely generated default random password=R1E8aWedaQVU6kKv for Keycloak root user stored at path=/tmp/QHUB_DEFAULT_PASSWORD
```

The password will also be available in the `qhub-config.yaml` file under the `security.keycloak.initial_root_password` field. It will be needed in the next page of these docs for logging in to your QHub.

<a href="#" name="project-naming-convention"></a>
> Note: **Project Naming Convention**
>
> In order to successfully deploy QHub, there are some project naming conventions which need to be followed. For starters,
make sure your name is compatible with the specific one for your chosen Cloud provider. In addition, QHub `projectname`
should also obey to the following format requirements:
> + letters from A to Z (upper and lower case) and numbers;
> + Special characters are **NOT** allowed;
> + Maximum accepted length of the name string is 16 characters.
> + If using AWS names **SHOULD NOT** start with the string `aws`

### Understanding the qhub-config.yaml file

The `qhub init` command may have some side-effects such automatically creating a GitHub repository and setting some repo secrets (if you used the `--repository-auto-provision` flag), and creating an Auth0 app, but the main output of the command is the `qhub-config.yaml` file.

This file is the configuration file that will determine how the cloud infrastructure and QHub is built and deployed in the next step.

But at this point it is just a text file! You could edit it manually if you are unhappy with the choices, or delete it and start over again.

Or it would be possible to create from scratch or re-use a `qhub-config.yaml` file - it is not essential to use `qhub init` at all, but it is often the easiest way to get started.

To understand some ways in which you could decide to edit the YAML file, see [Advanced Configuration](configuration.md).

## Deploy QHub

Finally, we can deploy QHub with:

```shell
qhub deploy -c qhub-config.yaml --dns-provider cloudflare --dns-auto-provision
```

Please omit `--dns-provider cloudflare --dns-auto-provision` if you are not using Cloudflare and will set up your DNS manually.

The command will create the following folder structure, which is the Terraform definition language for the QHub platform that will be deployed:

```
.
├── environments        # stores the conda environments
├── image               # docker images used on deployment: jupyterhub, jupyterlab, and dask-gateway
│   ├── dask-worker
│   ├── jupyterlab
│   └── scripts
├── infrastructure      # contains Terraform files that declare state of infrastructure
└── terraform-state     # required by terraform to securely store the state of the deployment
```

It will also start the deployment of your QHub, which will take around 10 minutes to complete.

Part of the output will show an "ip" address (DigitalOcean or GCP), or
a CNAME "hostname" (for AWS) according to the Cloud service
provider. Such as:

+ Digital Ocean/Google Cloud Platform
```shell
    ingress_jupyter = {
            "hostname" = ""
            "ip" = "xxx.xxx.xxx.xxx"
            }
```
+ AWS:
```shell
    ingress_jupyter = {
    "hostname" = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxx.us-east-1.elb.amazonaws.com"
    "ip" = ""
    }
```

If you specified `--dns-provider cloudflare --dns-auto-provision` on the command line, your DNS records for your domain should be updated automatically on Cloudflare. If you omitted those flags, you will be prompted to set the A/CNAME records manually on your domain name registrar's nameservers.

### GitOps

If you chose `--ci-provider github-actions` (or `gitlab-ci`) then QHub will use a GitHub Actions workflow (or GitLab equivalent) to automatically handle future deployment of
the infrastructure. For that to work, your newly generated project must be pushed to
GitHub. Using the URL under the `--repository` flag on the `qhub init`
command, you need to commit all files to the git repo.

To add the project to the initialized remote git repository run:

```shell
git add .github/ .gitignore environments/ image/ infrastructure/ qhub-config.yaml terraform-state/
git commit -m "First commit"
```

Push the changes to the repository (your primary branch may be called
`master` instead of `main`):

```shell
git push origin main
```

Once the files are in GitHub/GitLab, all CI/CD changes will be triggered by commits to main, and deployed via GitHub Actions or GitLab CI.  Since the infrastructure state is reflected in the repository, this workflow
allows for team members to submit pull requests that can be reviewed
before modifying the infrastructure, easing the maintenance process.

To automatically deploy:
- make changes to the `qhub-config.yaml` file on a new branch.
- create a pull request (PR) to main.
- Trigger the deployment by merging the PR. All changes will be
  automatically applied to the new QHub instance.

-----

Congratulations, you have now completed your QHub cloud deployment!

Having issues? Head over to our
[Troubleshooting](../admin_guide/troubleshooting.md) section for tips
on how to debug your QHub. Or try our
[FAQ](../admin_guide/faq.md).

If your deployment seemed to be successful, next learn how to [login](login.md).
