# Upgrade

Here we suppose a user would like to upgrade to a version `<version>`, probably the latest full release of [QHub on PyPI](https://pypi.org/project/qhub/).

You may be deploying QHub based on a local configuration file, or you may be using CI/CD workflows in GitHub or GitLab. Either way, you will need to locate a copy of your `qhub-config.yaml` configuration file to upgrade it (and commit back to your git repo in the CI/CD case).

For CI/CD deployments, you will need to `git clone <repo URL>` into a folder on your local machine if you haven't done so already.

## Step 1: Upgrade the `qhub` command package

To install (or upgrade) your pip installation of the Python package used to manage QHub:

```shell
pip install --upgrade qhub
```

The above will install the latest full version of QHub. For a specific older version use:

```shell
pip install --upgrade qhub==<version>
```

## Step 2: Upgrade `qhub-config.yaml` file

In the folder containing your QHub configuration file, run:

```shell
qhub upgrade -c qhub-config.yaml
```

This will output a newer version of `qhub-config.yaml` that's compatible with the new version of `qhub`. The process outputs a list of changes it has made. The `upgrade` command creates a copy of the original unmodified config file (`qhub-config.yaml.old.backup`) as well as a JSON file (`qhub-users-import.json`) used to import existing users into Keycloak.

## Step 3: Validate special customizations to `qhub-config.yaml`

You may have made special customizations to your `qhub-config.yaml`, such as using your own versions of Docker images. Please check your `qhub-config.yaml` and decide if you need to update any values that would not have been changed automatically - or, for example, you may need to build new versions of your custom Docker images to match any changes in QHub's images.

## Step 4: Redeploy QHub

If you are deploying QHub from your local machine (not using CI/CD) then you will now have a `qhub-config.yaml` file that you can deployed.

```shell
qhub deploy -m qhub-config.yaml
```

### CI/CD: render and commit to git

For CI/CD (GitHub/GitLab) workflows, then as well as generating the updated `qhub-config.yaml` files as above, you will also need to regenerate the workflow files based on the latest `qhub` version's templates.

With the newly upgraded `qhub-config.yaml` file, run:

```shell
qhub render -c qhub-config.yaml
```

(Note that `qhub deploy` would perform this render step too, but will also immediately redeploy your QHub.)

Commit all the files (`qhub-config.yaml` and GitHub/GitLab workflow files) back to the remote repo. All files need to be committed together in the same commit.

## (Step 5: Update OAuth callback URL for Auth0)

If your QHub deployment relies on Auth0 for authentication, please update the OAuth callback URL.

<details><summary>Click for more detailed instructions </summary>

1. Navigate to the your Auth0 tenacy homepage and from there select "Applications".

2. Select the "Regular Web Application" with the name of your deployment.

3. Under the "Application URIs" section, paste the new OAuth callback URL in the "Allowed Callback URLs" text block.
- The URL will take the shape:
    ```
    https://{your-qhub-domain}/auth/realms/qhub/broker/auth0/endpoint
    ```
    - Replace `{your-qhub-domain}` with the domain found in the `domain` section of your `qhub-config.yaml`.

</details>

## Step 6: Import users into Keycloak

The last two steps are to change the Keycloak `root` user password, documented [here](../installation/login.md#change-keycloak-root-password) and import existing users, documented [here](../admin_guide/backup.md#import-keycloak).

For more details on this process, visit the [Keycloak docs section](../installation/login.md).

## Known versions that require re-deployment

For versions that are known to error when upgrading, the steps for upgrade include:

- Deploy a new QHub with the desired version
- Back up user data and restore to the new cluster by following [this guide](https://docs.qhub.dev/en/stable/source/admin_guide/backup.html)
- Destroy old cluster

Version `v0.3.11` on AWS has an error with the kubernetes config map. See [this discussion](https://github.com/Quansight/qhub/discussions/841) for more details.
