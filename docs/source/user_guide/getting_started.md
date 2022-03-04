# Login to QHub

This guide aims to give a basic overview of the QHub login process. Your
organization's QHub will likely have a slightly different authentication
process due to the many authentication providers that QHub can integrate with.

The fisrt step is to connect with your QHub cluster, for this example we will
be using `https://qhub-demo.qhub.dev`. Once on the site, you will be prompted by a login, similar to the login page shown in the image below.

![QHub login screen](../images/qhub_login_screen.png)

Qhub now uses an open source tool called Keycloak for user managament. This makes it a little challenging to detail the exact process as it might differ greatly between authentication providers (LDAP, OAuth 2.0, passwordless authentication, password-based authentication and many others). A deeply overview of the QHub authentication process is described in the [Authentication Guide](../installation/login.mdl).

For this demonstration we will present the user with password-based or GitHub authentication.

![QHub Keycloak auth screen](../images/keycloak_qhub_login.png)

Once authenticated, the user will be forwarded to the main hub page. Where the user will have access to `Token` management, JupyterLab server access, and other features like `Dashboards` and `Admin` management.

![QHub main hub screen](../images/qhub_main_hub_page.png)

After `Start My Server` is selected, the user will be prompted with a set of profiles
that are available for the authenticated user to use. Your given
selections will likely differ from the image shown. The customized
profiles will give you access to fixed cloud resources for example 2 CPU, 8 GB RAM,
and 1 dedicated GPU, all of which is configured by your administrator, a more detailed explanation about dedicated profiles can be found in the [Profiles](../installation/configuration.md#profiles) section of advanced configuration.

![QHub select profile](../images/qhub_select_profile.png)

Once an appropriate profile has been select, click `start`. At this point, your JupyterHub will be launched, a step which may take up to several minutes due to QHub use of autoscaling under the hood. Ultimately this autoscaling feature helps reduce costs when the cluster is idle. A successful launch should look similar to the image below.

![QHub start server](../images/qhub_server_start.png)

Finally once the your JupyterHub instance has been launched you will notice a selection of available python environments. These environments will also represent the different kernel choices available for your notebooks, they are created and managed by conda-store and can be easily configured, more information at [Managing environments](../installation/configuration.md#environments).

![QHub kernel selection](../images/qhub_kernel_selection.png)

From the Launcher, with a double-click, you can launch a JupyterLab notebook with that given conda environment. Note that kernels can take several seconds to become responsive. The circle in the top right hand corner is a good indicator of the status of the kernel. A lightning bold means that the
kernel has started but it not yet ready to run code.
