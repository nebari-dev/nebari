# Usage

## Local Deployment

### Environment Variables
To deploy QHub set the environment variable `PYTHONPATH` and create a new sub-directory running:
```bash
export PYTHONPATH=$PWD:$PYTHONPATH
mkdir -p data
```

### Initialize configuration
Then, initialize the configuration file `qhub-config.yaml` with
```shell
python -m qhub init local --project=projectname --domain github-actions.qhub.dev --auth-provider=password --terraform-state=local
```

#### Generate user password
Each user on the `qhub-config.yaml` file will need a password. You can use [bcrypt](https://pypi.org/project/bcrypt/) to
generate a salted password by using the following python script:
```python
import bcrypt;

bcrypt.hashpw(b'<password>', bcrypt.gensalt())
```
Where `<password>` can be changed to any value.


TODO: describe this section with more precision. Where should the script be imported? Any exceptions for password characters?

### Render config file
Next, we will render the files from `qhub-config.yaml` running
```shell
python -m qhub render --config qhub-config.yaml -f
```

### Deploy modules

And finally, to deploy QHub:
```shell
python -m qhub deploy --config qhub-config.yaml --disable-prompt
```


To ease development we have already pointed the project's DNS record `jupyter.github-actions.qhub.dev` to the IP address 
`172.17.10.100`. TO make sure all is correctly set, check the load balancer IP address:
```shell
$ > load balancer ip command
```

In case the address does not correspond to `172.17.10.100`, point the DNS domain to the address by running
```ini
172.17.10.100 jupyter.github-actions.qhub.dev
```
### Verify deployment
Finally, if everything was set properly you should be able to cURL the JupyterHub server with
```shell
curl -k https://jupyter.github-actions.qhub.dev/hub/login
```

It is also possible to visit `https://jupyter.github-actions.qhub.dev` using the web browser.

### Cleanup
To clean up the installation use the command
```shell
python -m qhub destroy --config qhub-config.yaml 
```
Followed by 
```shell
minikube delete
```
The commands will delete all instances of QHub.

---

## Cloud Deployment

Once all environment variables have been set, you will be able to run commands on your terminal to set QHub's deployment.

### Initialize configuration
There are several ways to generate your configuration file. You can type your commands according to the terminal prompts,
or you can set it all automatically from the start. In any case, we advise you to start by creating a new project folder.

On your terminal run:
```shell
mkdir qhub-test && cd qhub-test
``` 

#### Fully automated deployment
To generate a fully automated deployment, on your terminal run:
```shell
qhub init aws --project project-name --domain jupyter.qhub.dev --ci-provider github-actions --oauth-provider auth0 
--oauth-auto-provision --repository github.com/quansight/project-name --repository-auto-provision
```
The command above will generate the `qhub-config.yaml` config file with an infrastructure deployed on `aws`, named 
`project-name`, where the domain will be `jupyter.qhub.dev`. The deployment will use `github-actions` as the continuous integration (CI)
provider, automatically provisioned and authenticated by `auth0`, initialized on GitHub under the URL `github.com/quansight/project-name `.

<p> **I am not 100% sure how to detail this part.**

There are several **optional** (yet highly recommended) flags that allow to configure the deployment:

+ `aws` indicates that the project will be deployed on the Amazon AWS Cloud provider.
- `--project`: project-name is required to be a string compliant with the Cloud provider recommendations (see official provider docs).
  + `jupyter.qhub.dev` is the domain registered on CloudFlare. In case you chose not to use Cloudflare, skip this flag.
- `--domain`: base domain for your cluster. After deployment, the DNS will use the base name prepended with `jupyter`. IE if the base name is `test.qhub.dev` then the DNS will be provisioned as `jupyter.test.qhub.dev`. This pattern is also applicable if you are setting your own DNS through a different provider.
- `--ci-provider`: This specifies what provider to use for CI/CD. Currently, GitHub Actions is supported.
- `--oauth-provider`: This will set configuration file to use Auth0 for authentication
- `--oauth-auto-provision`: This will automatically create and configure an Auth0 application
- `--repository`: The repository name that will be used to store the Infrastructure-as-Code
- `--repository-auto-provision`: This sets the secrets for the GitHub repository

</p>


### Render config files
This file will handle the creating of all Terraform modules for QHub infrastructure.

After initializing, we then need to create all of Terraform configuration. This done by running the local command:
```shell
qhub render -c qhub-config.yaml -o ./ -f
```

This will create the following folder structure:
```txt
.
├── environments        # conda environments are stored
├── image               # docker images used in QHub deployment including: jupyterhub, jupyterlab, and dask-gateway
│   ├── dask-worker
│   ├── jupyterlab
│   │   └── __pycache__
│   └── scripts
├── infrastructure      # terraform files that declare state of infrastructure
└── terraform-state     # required by terraform to securely store the state of the Terraform deployment
```
        
### Deploy QHub

Finally, we can deploy QHub with:
```shell
qhub deploy -c qhub-config.yaml --dns-provider cloudflare --dns-auto-provision
```

The terminal will prompt to press `[enter]` to check oauth credentials (which were added by QHub init). After pressing `enter` the deployment will continue and take roughly 10 minutes. Part of the output will show an "ip" address (DO/GCP) or a CNAME "hostname" (AWS) based on the the cloud service provider:

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

        
### 2.8 Push repository

Add all files to github:

    git add .github/ .gitignore README.md environments/ image/ infrastructure/ qhub-config.yaml  terraform-state/

Push the changes to your repo:
```shell
git push origin main
```



## 3. Post GitHub deployment:

After the files are in Github all CI/CD changes will be triggered by a commit to main and deployed via GitHub actions. To use gitops, make a change to `qhub-ops.yaml` in a new branch and create a pull request into main. When the pull request is merged, it will trigger a deployment of all of those changes to your QHub.

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