# Step by Step QHub Cloud Deployment

1) **Create a GitHub repository and set your environment variables**
    - Clone your Github repository and in your terminal (or in your favorite IDE), `cd` into your it. 
    - Create an `.envrc` file and set your environment variables. For details about which environment variables you will need, please see your choice of provider below:
        - [AWS Environment Variables](https://github.com/Quansight/qhub/blob/ft-docs/docs/docs/aws/installation.md).
        - [Digital Ocean Environment Variables](https://github.com/Quansight/qhub/blob/ft-docs/docs/docs/do/installation.md)
        - [Google Cloud Platform](https://github.com/Quansight/qhub/blob/ft-docs/docs/docs/gcp/installation.md)
    - Set all your access keys for your variables for the cloud provider in the `.envrc` file. 
    - In your terminal, enter the command `direnv allow` to load all the tokens/keys you have listed in your environment file.
    - Commit and push your changes to your GitHub repository.

After this step, you are ready to initialize `QHub`

2) **Initialize QHub**
    - In your terminal, enter the command `qhub init` followed by the abbreviation of your cloud provider. (do: Digital Ocean, aws: Amazon Web Services, gcp: Google Cloud Platform). Example `qhub init do` to initiate QHub for a Digital Ocean deployment. This will build QHub and create  a `qhub-config.yaml` file in your folder. 
    - Open the config file, and under the `security` section, add your github username and add a `uid` your your username. 
    - Set the `domain` field on top of the config file to `<abbreviation-of-your-cloud-provider>.qhub.dev`
    - You need to get a CLIENT_ID and CLIENT_SECRET ID. This needs to be your access token for github. 
        - In your Github account, while you are creating a token, check `repo` and `workflow` options in the scopes. 
    - Copy the personal access token you generated in Github in the Github Secrets; this will be your `REPOSITORY_ACCESS_TOKEN`
    - Register a new `OAuth` application in Github, In here, copy and paste the address in your `domain` in the config file. 

   **Build QHub**
    - In your terminal, enter the command `qhub-render -c qhub qhub.config.yaml -o ./ -f`
    - With this command, all the files for deployment will be created. 
    - `ls` to see all the files that have been created.
    - Commit your changes to your github repo. 

3) **DNS Settings and Deployment**
    - To deploy the QHub instance to your cloud server, type the command `python scripts/00-guided-install.py` This process will take a few minutes. 
        - If your provider is Digital Ocean, before you run the command above, you will need to update DO with the command `doctl kubernetes options versions` to get the latest evrsion for DO. Open your `qhub-config.yaml` file and enter the kubernetes version that the above command outputs for `kubernetes_version` under `digital_ocean` section of your config file. 
- You should be able to see your deployment in your DO dashboard in a few minutes after the above steps. 

At this stage, you need to set up DNS to point to your qhub instance.

**DNS Settings**
- To set up your DNS, you will need a [Cloudflare](https://support.cloudflare.com/hc/en-us/articles/360019093151-Managing-DNS-records-in-Cloudflare#h_60566325041543261564371) account. 
- After the build process in the previous section successfully completes, you will see an IP address in your terminal. Go to your Cloudflare account, and click on "add a record." 
- Name your record, as `jupyter.<abbreviation-for-your-cloud-provider>`, or any other name you would like to use, and click on **Proxy Status** 
- You can check on your DNS status with the command `dig` followed by the qhub url for your instance while waiting for the DNS setup to complete. This might take a while because qhub makes sure everyhting in the cluster and the DNS sesstings works successfully.
- If this process completes successfully, you can be confident that everything works properly in the cluster. 
- After DNS setup completes, commit your changes to your Github repo. 


Congratulations! You have now completed your QHub cloud deployment!