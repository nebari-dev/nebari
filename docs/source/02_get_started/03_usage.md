# Usage

## Cloud Deployment

Once all environment variables have been set, you will be able to run commands on your terminal to set QHub's deployment.

### Initialize configuration
There are several ways to generate your configuration file. You can type your commands according to the terminal prompts,
or you can set it all automatically from the start. In any case, we advise you to start by creating a new project folder.
Here, we will name the new folder `qhub-test`.

On your terminal run:
```shell
mkdir qhub-test && cd qhub-test
``` 

#### Fully automated deployment
To generate a fully automated deployment, on your terminal run:
```shell
qhub init aws --project project-name --domain jupyter.qhub.dev --ci-provider github-actions --auth-provider auth0 
--auth-auto-provision --repository github.com/quansight/project-name --repository-auto-provision
```
The command above will generate the `qhub-config.yaml` config file with an infrastructure deployed on `aws`, named 
`project-name`, where the domain will be `jupyter.github-actions.qhub.dev`. The deployment will use `github-actions` 
as the continuous integration (CI) provider, automatically provisioned and authenticated by `auth0`, initialized on 
GitHub under the URL `github.com/quansight/project-name `.


There are several **optional** (yet highly recommended) flags that allow to configure the deployment:

+ `aws` indicates that the project will be deployed on the Amazon AWS Cloud provider.
- `--project`: project-name is required to be a string compliant with the Cloud provider recommendations (see official Cloud provider docs on naming policies).
  + `jupyter.qhub.dev` is the domain registered on CloudFlare. In case you chose not to use Cloudflare, skip this flag.
- `--domain`: base domain for your cluster. After deployment, the DNS will use the base name prepended with `jupyter`, i.e.
  if the base name is `test.qhub.dev` then the DNS will be provisioned as `jupyter.test.qhub.dev`. This pattern is also applicable if you are setting your own DNS through a different provider.
- `--ci-provider`: specifies what provider to use for CI/CD. Currently, only supports GitHub Actions.
- `--auth-provider`: This will set configuration file to use the specified provider for authentication.
- `--auth-auto-provision`: This will automatically create and configure an application using OAuth.
- `--repository`: Repository name that will be used to store the Infrastructure-as-Code on GitHub.
- `--repository-auto-provision`: Sets the secrets for the GitHub repository used for CI/CD actions.


### Render config files
This file will handle the creation of all Terraform modules for the QHub infrastructure.

After initializing, we then need to create all Terraform configuration. This done by running the local command:
```shell
qhub render -c qhub-config.yaml -o ./ -f
```

This will create the following folder structure:
```
.
├── environments        # stores the conda environments
├── image               # docker images used on deployment: jupyterhub, jupyterlab, and dask-gateway
│   ├── dask-worker
│   ├── jupyterlab
│   │   └── __pycache__
│   └── scripts
├── infrastructure      # contains Terraform files that declare state of infrastructure
└── terraform-state     # required by terraform to securely store the state of the deployment
```
        
### Deploy QHub

Finally, we can deploy QHub with:
```shell
qhub deploy -c qhub-config.yaml --dns-provider cloudflare --dns-auto-provision
```

The terminal will prompt to press `[enter]` to check auth credentials (which were added by the `qhub init` command). 
That will trigger the deployment which will take around 10 minutes to complete.

Part of the output will show an "ip" address (DigitalOcean or GCP), or a CNAME "hostname" (for AWS)
according to the Cloud service provider. Such as:

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
QHub uses a GitHub Action to automatically handle the deployment of the infrastructure. For that, the project must be 
pushed to GitHub. Using the URL under the `--repository` flag on the `qhub init` command, set the CI/CD changes to be triggered.

To add the project to the initialized GitHub repository run:
```shell
git add .github/ .gitignore environments/ image/ infrastructure/ qhub-config.yaml terraform-state/
git commit -m "First commit"
```

Push the changes to the repository (your primary branch may be called `master` instead of `main`):
```shell
git push origin main
```

Once the files are in Github, all CI/CD changes will be triggered by commits to main, and deployed via GitHub actions.
Since the infrastructure state is reflected in the repository, this workflow allows for team members to submit pull 
requests that can be reviewed before modifying the infrastructure, easing the maintenance process.

To automatically deploy:
- make changes to the `qhub-config.yaml` file on a new branch. 
- create a pull request (PR) to main.
- Trigger the deployment by merging the PR. All changes will be automatically applied to the new QHub instance.

Congratulations, you have now completed your QHub cloud deployment! :tada

Having issues? Head over to our [Troubleshooting](../02_get_started/06_troubleshooting.md) section for tips on how to 
debug your QHub. Or try our [FAQ](../02_get_started/07_support.md).
