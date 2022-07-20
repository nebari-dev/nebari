---
id: login-keycloak
title: How to authenticate using Keycloak and launch your server
description: |
  This is a how-to for authenticating using Keycloak.
---

This guide aims to give a basic overview of the Nebari login process. Your organization's Nebari deployment will likely have a slightly different process due to the many
authentication providers that Nebari can integrate with.

1. Connect to your Nebari cluster, as an example your cluster domain should look like `https://nebari-demo.nebari.dev`.

Once on the site, you will be prompted by a login, similar to
the login page shown in the image below.

![Nebari login screen](/img/how-tos/nebari_login_screen.png)

Nebari now uses an open source tool called [Keycloak](https://www.keycloak.org/) for user management. This makes it a little challenging to detail the exact process as it might differ greatly between
authentication providers ([LDAP](https://pt.wikipedia.org/wiki/LDAP), [OAuth 2.0](https://oauth.net/2/), passwordless authentication, password-based authentication and many others). For more information on how to configure Keycloak, and add new users, make sure to check [How to configure Keycloak and add new users](/how-tos/configuring-keycloak) sections of our docs.

2. Authentication will differ based on the [Identity providers](https://www.keycloak.org/docs/latest/server_admin/#_identity_broker) chosen by your organization, in this example, we will use a simple password-based authentication.

![Nebari Keycloak auth screen](/img/how-tos/keycloak_nebari_login.png)

Once authenticated, you will be forwarded to the main hub page where you have access to `Token` management, JupyterLab server access, and other features like
`Dashboards` and `Admin` management.

![Nebari main hub screen](/img/how-tos/nebari_main_hub_page.png)

3. Now, click in `Start My Server`, you will be prompted with a set of profiles that are available for the authenticated user. Your given selections will likely differ from
the image shown.

The customized profiles will give you access to fixed cloud resources. For example, you could choose a resource with 2 CPUs, 8 GB RAM, and 1 dedicated GPU, all of
which is configured by your administrator. A more detailed explanation of dedicated profiles can be found in the [Profiles] section of
the advanced configuration page.

![Nebari select profile](/img/how-tos/nebari_select_profile.png)

4. Once an appropriate profile has been selected, click `start`. At this point, your JupyterHub instance will be launched, a step which may take up to several minutes due to Nebari use
of autoscaling under the hood.

Ultimately this autoscaling feature helps reduce costs when the cluster is idle. A successful launch should look similar to the image below.

![Nebari start server](/img/how-tos/nebari_server_start.png)

Once your JupyterHub instance has been launched you will notice a selection of available Python environments. These environments will also represent the different kernel choices
available for your notebooks. They are created and managed by conda-store and can be easily configured. Learn more at
[Managing environments].

![Nebari kernel selection](/img/how-tos/nebari_kernel_selection.png)

From the Launcher, you can choose a JupyterLab notebook with a given conda environment. Note that kernels can take several seconds to become responsive. The circle in the top
right-hand corner is a good indicator of the status of the kernel. A lightning bold means that the kernel has started, but it is not yet ready to run code. An open circle means
it's ready.