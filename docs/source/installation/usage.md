# Usage

## Cloud Deployment

Once all environment variables have been set, you will be able to run
commands on your terminal to set QHub's deployment.

### Initialize configuration

There are several ways to generate your configuration file. You can
type your commands according to the terminal prompts, or you can set
it all automatically from the start. In any case, we advise you to
start by creating a new project folder.  Here, we will name the new
folder `qhub-test`.

On your terminal run:

```shell
mkdir qhub-test && cd qhub-test
```

#### Fully automated deployment

To generate a fully automated deployment, on your terminal run:

```shell
qhub init aws --project projectname --domain qhub.dev --ci-provider github-actions --auth-provider auth0
--auth-auto-provision --repository github.com/quansight/project-name --repository-auto-provision
```

The command above will generate the `qhub-config.yaml` config file
with an infrastructure deployed on `aws`, named `projectname`, where
the domain will be `qhub.dev`. The deployment
will use `github-actions` as the continuous integration (CI) provider,
automatically provisioned and authenticated by `auth0`, initialized on
GitHub under the URL `github.com/quansight/projectname`.

There are several **optional** (yet highly recommended) flags that
allow to configure the deployment:

- `aws` indicates that the project will be deployed on the Amazon AWS Cloud provider.
    + Optional flags are: `gcp`, `do` and `azure`.
- `--project`: the name of the project is required to be a string compliant with the Cloud provider recommendations. For
  more details see official Cloud provider docs on naming policies and check our docs on [naming convention](#project-naming-convention).
- `--domain`: base domain for your cluster. This pattern is also applicable if you are setting your own DNS through a different provider.
  + `jupyter.qhub.dev` is the domain registered on CloudFlare. In case you chose not to use Cloudflare, skip this flag.
- `--ci-provider`: specifies what provider to use for CI/CD. Currently, supports GitHub Actions, GitLab CI, or none.
- `--auth-provider`: This will set configuration file to use the specified provider for authentication.
- `--auth-auto-provision`: This will automatically create and configure an application using OAuth.
- `--repository`: Repository name that will be used to store the Infrastructure-as-Code on GitHub.
- `--repository-auto-provision`: Sets the secrets for the GitHub repository used for CI/CD actions.

##### Project Naming Convention
In order to successfully deploy QHub, there are some project naming conventions which need to be followed. For starters,
make sure your name is compatible with the specific one for your chosen Cloud provider. In addition, QHub `projectname`
should also obey to the following format requirements:
+ letters from A to Z (upper and lower case) and numbers;
+ Special characters are **NOT** allowed;
+ Maximum accepted length of the name string is 16 characters.

+ If using AWS:
  - names **SHOULD NOT** start with the string `aws`;

### Deploy QHub

Finally, we can deploy QHub with:

```shell
qhub deploy -c qhub-config.yaml --dns-provider cloudflare --dns-auto-provision
```

This will create the following folder structure:

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

The terminal will prompt to press `[enter]` to check auth credentials
(which were added by the `qhub init` command).  That will trigger the
deployment which will take around 10 minutes to complete.

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

Once the files are in GitHub, all CI/CD changes will be triggered by
commits to main, and deployed via GitHub actions.  Since the
infrastructure state is reflected in the repository, this workflow
allows for team members to submit pull requests that can be reviewed
before modifying the infrastructure, easing the maintenance process.

To automatically deploy:
- make changes to the `qhub-config.yaml` file on a new branch.
- create a pull request (PR) to main.
- Trigger the deployment by merging the PR. All changes will be
  automatically applied to the new QHub instance.

Congratulations, you have now completed your QHub cloud deployment!

Having issues? Head over to our
[Troubleshooting](../admin_guide/troubleshooting.md) section for tips
on how to debug your QHub. Or try our
[FAQ](../admin_guide/faq.md).
