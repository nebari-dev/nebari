# Usage

## Cloud Deployment

Great, you've gone through the `qhub` [Installation](installation.md) and [Setup Initialization](setup.md) steps,
and have ensured that all the necessary environment variables have been properly set, it's time to deploy QHub
from your terminal.

### Initialize configuration

There are several ways to generate your configuration file. You can
type the commands when prompted by terminal, or you can set
it all automatically from the start. In any case, start by creating
a new project folder.  Start by creating a directory `qhub-test`.

On your terminal run:

```shell
mkdir qhub-test && cd qhub-test
```

#### Fully automated deployment

To generate a fully automated configuration file, on your terminal run:

```shell
qhub init aws --project projectname --domain qhub.dev --ci-provider github-actions --auth-provider auth0
--auth-auto-provision --repository github.com/quansight/project-name --repository-auto-provision
```
There are several **optional** (yet highly recommended) flags that
allow to configure the deployment:

- `aws` indicates the QHub is going to be deployed on the Amazon AWS Cloud provider.
    + Other optional flags include: `gcp`, `do` and `azure`.
- `--project`: the name of the project is required to be a string compliant with the Cloud provider recommendations. For
  more details see official Cloud provider docs on naming policies and see below on the [project naming convention](#project-naming-convention).
- `--domain`: base domain for your cluster. This pattern is also applicable if you are setting your own DNS through a different provider.
  + `qhub.dev` is the domain registered on CloudFlare. If you chose not to use Cloudflare, skip this flag.
- `--ci-provider`: specifies what provider to use for CI/CD. Currently, supports GitHub Actions, GitLab CI, or none.
- `--auth-provider`: Used to specified authentication provider, in this case Auth0
- `--auth-auto-provision`: Whether or not to automatically create and configure the authentication provider.
- `--repository`: Repository name used to store the Infrastructure-as-Code on GitHub.
- `--repository-auto-provision`: Sets the secrets for the GitHub repository used for CI/CD actions.

The command above generates the `qhub-config.yaml` config file
with an infrastructure deployed on `aws`, named `projectname`, with a
domain name set to `qhub.dev`. The deployment uses `github-actions` as
the continuous integration (CI) provider,
automatically provisioned and authenticated by `auth0`, initialized on
GitHub under the URL `github.com/quansight/projectname`.

If employing an infrastructure-as-code approach, this is where you would make the desired infrastructure changes
including adding users, changing Dask worker instance type and much more. Once you're happy with your changes you would redeploy those changes using using GitHub Actions. For more details on on the `qhub-config.yaml` please see [Configuration](configuration.md)

##### Project Naming Convention
In order to successfully deploy QHub, please follow some project naming conventions. For starters,
make sure your project name is compatible with the specifics of your chosen cloud provider. In addition, QHub `projectname`
should also obey to the following format requirements:
+ letters from A to Z (upper and lower case) and numbers;
+ Special characters are **NOT** allowed;
+ Maximum accepted length of the name string is 16 characters.

+ If using AWS:
  - names **SHOULD NOT** start with the string `aws`;

### Deploy QHub

Finally, with the `qhub-config.yaml` created, QHub can be deployed for the first time:

```shell
qhub deploy -c qhub-config.yaml --dns-provider cloudflare --dns-auto-provision
```

This creates the following folder structure:

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

The terminal then prompts you to press `[enter]` to check auth credentials
(which were added by the `qhub init` command).  This triggers the
deployment, which takes around 10 minutes to complete.

During the initial deployment, Digital Ocean, GCP and Azure are going to display an `"ip"` address
whereas AWS is going to display a CNAME `"hostname"`.

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

### GitOps

QHub uses a GitHub Action to automatically handle the deployment of
the infrastructure. For that, the project must be pushed to
GitHub. Using the URL under the `--repository` flag on the `qhub init`
command, set the CI/CD changes to be triggered.

To add the project to the initialized GitHub repository run:

```shell
git add .github/ .gitignore environments/ image/ infrastructure/ qhub-config.yaml terraform-state/
git commit -m "First commit"
```

Push the changes to the repository (your primary branch may be called
`master` instead of `main`):

```shell
git push origin main
```

Once pushed to GitHub, future commits to `main`  trigger CI/CD to redeploy
changes the QHub clusger.  Since the infrastructure state is reflected in
the repository, this workflow allows for team members to submit pull requests
that can be reviewed before modifying the infrastructure, easing the
maintenance process.

To automatically deploy (and to keep track of changes more effectively):
- make changes to the `qhub-config.yaml` file on a new branch.
- create a pull request (PR) to main.
- Trigger the deployment by merging the PR and changes are
  automatically applied to the QHub cluster.

Congratulations, you have now completed your QHub cloud deployment!

Having issues? Head over to our
[Troubleshooting](../admin_guide/troubleshooting.md) section for tips
on how to debug your QHub. Or try our
[FAQ](../admin_guide/faq.md).
