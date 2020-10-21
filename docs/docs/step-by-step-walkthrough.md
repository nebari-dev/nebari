# Step by Step QHub Cloud Deployment

This guide makes the following assumptions:

- [Github actions] will be used for CICD
- Oauth will be [via github] using [auth0]
- DNS registry will be through [Cloudflare]

Other providers can be used, but you will need consult their documention on setting up oauth and DNS registry.


## 1. Installing QHub:

* Via github:

    ```
    git clone git@github.com:Quansight/qhub.git
    cd qhub
    python ./setup.py install
    ```

* Via pip:
    ```
    pip install qhub
    ```

## 2. Configuration

### 2.1. **Environment variables**

Set the required environment variables based on your choice of provider:

- AWS:    (Old instructions for reference: [AWS Environment Variables])
    
    * `AWS_ACCESS_KEY_ID`
    * `AWS_SECRET_ACCESS_KEY`
    * `AWS_DEFAULT_REGION`

- [Digital Ocean Environment Variables]
- [Google Cloud Platform]

After this step, you are ready to initialize `QHub`

### 2.2. **DNS: Optionally Create a Cloudflare account**
    
This step is necessary if you don't have a DNS with an existing domain for which you can make `CNAME` or `A` entries.

To set up your DNS and automatically get a certificate, you can create a [Cloudflare][Cloudflare_signup] account and register a [domain name]. 

### 2.3. **Initialize and Configure QHub**

In your terminal, where the environment variables from Step **1** are set, enter the command `qhub init` followed by the abbreviation of your cloud provider. (do: Digital Ocean, aws: Amazon Web Services, gcp: Google Cloud Platform). This will create  a `qhub-config.yaml` file in your folder.


        $ qhub init do    # Digital Ocean
        $ qhub init aws   # Amazon Web Services
        $ qhub init gcp   # Google Cloud Platform
     

Open the config file `qhub-config.yaml` for editing.

#### Top section:

Chose a `project_name` that is a compliant name. E.g. a valid bucket name for AWS.

        project_name: my-jupyterhub

Set the `domain` field on top of the config file to a domain or sub-domain you own in Cloudflare or your existing DNS, e.g. `testing.qhub.dev`: 

        domain: testing.qhub.dev
        
#### `security` section:

Create an [oauth application] in github and fill in the client_id and client_secret.
             
        client_id: "7b88..."
        client_secret: "8edd7f14..."
      
Set the `oauth_callback_url` by prepending your domain with `jupyter` and appending `/hub/oauth_callback`. Example:
    
        oauth_callback_url: https://jupyter.testing.qhub.dev/hub/oauth_callback

Add your and optionally other `github username(s)` (or the usernames used with your `oauth` application), set a unique `uid` for each username, and set `primary_group` and optionally `secondary_groups` affiliations for the user:
         

        costrouc:
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
        
    
        $ doctl kubernetes options versions
        Slug            Kubernetes Version
        1.18.8-do.1     1.18.8
        1.17.11-do.1    1.17.11
        1.16.14-do.1    1.16.14
   
    
    Copy the first line under `Slug` which is the latest version. Enter it into the `kubernetes_version` under the `digital_ocean` section of your config file. 
    
        kubernetes_version: 1.18.8-do.1
    

### 2.4. Render QHub
    
The render step will use `qhub_config.yaml` as a template to create an output folder and generate all the necessary files for deployement. 
    
    The below example will create the directory `qhub-deployment` and fill it with the necessary files.

    
        $ qhub render -c qhub_config.yaml -o qhub-deployment -f
    
    
    Move the config file into the output directory
        
    
        $ mv qhub_config.yaml qhub-deployment/
    

## 3. Deployment and DNS registry

The following command  will check environment variables, deploy the infrastructure, and prompt for DNS registry

        $ qhub deploy -c qhub_config.yaml 

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

