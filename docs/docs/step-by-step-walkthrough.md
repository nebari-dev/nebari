Tokens needed for all cloud providers:

        export CLOUDFLARE_TOKEN=
        export AUTH0_DOMAIN=
        export AUTH0_CLIENT_ID=
        export AUTH0_CLIENT_SECRET=
        export GITHUB_USERNAME=
        export GITHUB_TOKEN=
        Google specific providers:

        export PROJECT_ID=
        export GOOGLE_CREDENTIALS=/tmp/quansight-internal-it-credentials.json



# Step by Step QHub Cloud Deployment

This guide makes the following assumptions:

- [Github actions] will be used for CICD
- Oauth will be via [auth0]
- DNS registry will be through [Cloudflare]

Other providers can be used, but you will need to consult their documention on setting up oauth and DNS registry. If a different provider is desired, then the corresponding flag in the `qhub` command line argument can be ommited.

## 1. Installing QHub:

- Via github:

        git clone git@github.com:Quansight/qhub.git
        cd qhub
        python ./setup.py install

- Via pip:

        pip install qhub

## 2. Environment variables

Several different environment variables must be set in order for deployment to be fully automated. The following subsections will describe the purpose and method for obtaining the values for these variables.

### 2.1 Cloudflare

Cloudflare will automate the DNS registration. First a [Cloudflare][Cloudflare_signup] account needs to be created and [domain name] registered through it. If an alternate DNS provider is desired, then omit the `--dns-provider cloudflare` flag for `qhub deploy`. At the end of deployement an IP address (or CNAME for AWS) will be output that can be registered to your desired URL.

Within your Cloudflare account, follow these steps to generate a token

- Click user icon on top right and click `My Profile`
- Click the `API Tokens` menu and select `Create Token`
- Click `Use Template` next to `Edit zone DNS`
- Under Zone Resources select the DNS that you control
- Click continue to summary
- Click Create Token
- `CLOUDFLARE_TOKEN`: Set this variable equal to the token generated

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

### 2.3 Github
Your github username and access token will automate the creation of the repository that will hold the infrastructure code as well as the github secrets

- `GITHUB_USERNAME`: Set this to your github username
- `GITHUB_TOKEN`: Set this equal to your [github access token]


### 2.4 Cloud Provider Credentials
The access key for the cloud providers require fairly wide permissions in order for QHub to deploy. As such, all testing for QHUb has been done with owner/admin level permissions. We welcome testing to determine the minimum required permissions for deployment [(open issue)](https://github.com/Quansight/qhub/issues/173).

#### 2.4.1 Amazon Web Services

Please see these instructions for [creating an IAM role] with admin permissions and set the below variables.
    
- `AWS_ACCESS_KEY_ID`: The public key for an IAM account
- `AWS_SECRET_ACCESS_KEY`: The Private key for an IAM account
- `AWS_DEFAULT_REGION`: The region where you intend to deploy QHub

#### 2.4.2 Digital Ocean

In order to get the DigitalOcean access keys follow this [digitalocean tutorial].

- `DIGITALOCEAN_TOKEN`: Follow [these instructions] to create a digital ocean token 
- `SPACES_ACCESS_KEY_ID`: Follow [this guide] to create a spaces access key/secret
- `SPACES_SECRET_ACCESS_KEY`: The secret from the above instructions
- `AWS_ACCESS_KEY_ID`: Due to a [terraform] quirk, set to the same as `SPACES_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`: Due to the quirk, set to the same as `SPACES_SECRET_ACCESS_KEY`

#### 2.4.3 Google Cloud Platform

Follow [these detailed instructions] on creating a Google service account with owner level permissions. With the service account created, follow [these steps] to create and download a json credentials file.

- `GOOGLE_CREDENTIALS`: Set this to the path to your credentials file
- `PROJECT_ID`: Set this to the project ID listed on the home page of your Google console under `Project info`

We're done with the hardest part of deployment!

### 2.5 QHub init

With all of the applicable environment variables set, we are ready to get into the wizardry that QHub performs. The first command `qhub init` followed by the abbreviation of your cloud provider. (do: Digital Ocean, aws: Amazon Web Services, gcp: Google Cloud Platform). This will create  a `qhub-config.yaml` file in your folder.


        $ qhub init do    # Digital Ocean
        $ qhub init aws   # Amazon Web Services
        $ qhub init gcp   # Google Cloud Platform
     

Open the config file `qhub-config.yaml` for editing.

#### Top section:

Chose a `project_name` that is a compliant name. E.g. a valid bucket name for AWS.

        project_name: my-jupyterhub

Set the `domain` field on top of the config file to a domain or sub-domain you own in Cloudflare or your existing DNS, e.g. `testing.qhub.dev`: 

        domain: testing.qhub.dev
        
#### security section:

Create an [oauth application] in github and fill in the client_id and client_secret.
             
        client_id: "7b88..."
        client_secret: "8edd7f14..."
      
Set the `oauth_callback_url` by prepending your domain with `jupyter` and appending `/hub/oauth_callback`. Example:
    
        oauth_callback_url: https://jupyter.testing.qhub.dev/hub/oauth_callback

Add your desired list of authorized github usernames. Set a unique `uid` for each username, and set the `primary_group`. Optional `secondary_groups` may also be set for each user:

        joeuser:
            uid: 1000000
            primary_group: users
            secondary_groups:
                - billing
                - admin
        janeuser:
            uid: 1000001
            primary_group: users

             
#### Cloud provider section:

Lastly, make the adjusted changes to configure your cluster in he cloud provider section.



**(Digital Ocean only)**
    
If your provider is Digital Ocean you will need to install [doctl] and obtain the latest kubernetes version. After installing, run this terminal command:
        
```bash
    $ doctl kubernetes options versions
    Slug            Kubernetes Version
    1.18.8-do.1     1.18.8
    1.17.11-do.1    1.17.11
    1.16.14-do.1    1.16.14
```
    
Copy the first line under `Slug` which is the latest version. Enter it into the `kubernetes_version` under the `digital_ocean` section of your config file. 
    
        kubernetes_version: 1.18.8-do.1
    

### 2.4. Render QHub
    
The render step will use `qhub-config.yaml` as a template to create an output folder and generate all the necessary files for deployement. 
    
The below example will create the directory `qhub-deployment` and fill it with the necessary files.

    
    $ qhub render -c qhub-config.yaml -o qhub-deployment -f
    
    
Move the config file into the output directory
        
    $ mv qhub-config.yaml qhub-deployment/

## 3. Deployment and DNS registry

The following command  will check environment variables, deploy the infrastructure, and prompt for DNS registry

        $ qhub deploy -c qhub-config.yaml 

Press `enter` to verify the oauth has been configured. The first stage of deployment will begin and there will be many lines of output text. After a few minutes, you will be prompted to set your DNS. This output will show an "ip" address (DO/GCP) or a CNAME "hostname" (AWS) based on the the cloud service provider:

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

Then you will be prompted with 

    Take IP Address Above and update DNS to point to "jupyter.testing.qhub.dev" [Press Enter when Complete]
    
Login to your DNS provider and make the DNS entry with the information above. For AWS add a CNAME, for DO and GCP add a type "A" entry. 
When [recording your DNS] on Cloudflare, click on **Proxy Status** and change it to **DNS only**.
 
When the DNS entries are made, wait until the DNS has been updated. You can check on your DNS status with the linux command `dig` followed by your url. The ip address or CNAME will show in the output of the command when DNS registry is complete.

Press **Enter** when the DNS is registered to complete the deployment.


## 4. **Set up  github repository**

Create a github personal access token ([github_access_token]) and check the `repo` and `workflow` options under scopes.

Copy the personal access token Github Secrets with the label `REPOSITORY_ACCESS_TOKEN`

All other environment variables that were created in step **1** also need to be added to github as secrets

Create a github repo and push all files to it with the following commands:

```
$ git init
$ git remote add origin <repo_url>
$ git add *
$ git commit -m 'initial commit'
$ git push origin master
```

## 5. **Git ops enabled**
Since the infrastructure state is reflected in the repository, it allows self-documenting of infrastructure and team members to submit pull requests that can be reviewed before modifying the infrastructure.

To use gitops, make a change to the `qhub-ops.yaml` in a new branch and create pull request into master. When the pull request is merged, it will trigger a deployement of all of those changes to your qhub.

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