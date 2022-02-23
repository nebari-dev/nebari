# Upgrade

This is a guide to the general upgrade of QHub to a new version.

You should always [backup your data](./backup.md) before upgrading.

> Note that for some releases (e.g. to v0.4), the cluster cannot be upgraded in-situ so you must perform a redeployment (backup the old cluster, redeploy a new upgraded cluster and then restore your data).
>
> To perform a redeployment upgrade see the [breaking upgrade documentation](./breaking-upgrade.md).

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

This will output a newer version of `qhub-config.yaml` that's compatible with the new version of `qhub`. The process outputs a list of changes it has made. The `upgrade` command creates a copy of the original unmodified config file (`qhub-config.yaml.old.backup`) as well as any other files that may be required by the upgraded cluster (if any).

## Step 3: Validate special customizations to `qhub-config.yaml`

You may have made special customizations to your `qhub-config.yaml`, such as using your own versions of Docker images. Please check your `qhub-config.yaml` and decide if you need to update any values that would not have been changed automatically - or, for example, you may need to build new versions of your custom Docker images to match any changes in QHub's images.

## Step 4: Redeploy QHub

If you are deploying QHub from your local machine (not using CI/CD) then you will now have a `qhub-config.yaml` file that you can deploy.

```shell
qhub deploy -c qhub-config.yaml
```

At this point you may see an error message saying that deployment is prevented due to the `prevent_deploy` setting in your YAML file. This is a safeguard to ensure that you only proceed if you are aware of possible breaking changes in the current upgrade.

For example, we may be aware that you will lose data due to this upgrade, so need to note a specific upgrade process to keep your data safe. Always check the release notes of the release in this case and get in touch with us if you need assistance. For example, you may find that your existing cluster is intentionally deleted so that a new replacement can be deployed instead, in which case your data must be backed up so it can be restored after the upgrade.

### CI/CD: render and commit to git

For CI/CD (GitHub/GitLab) workflows, then as well as generating the updated `qhub-config.yaml` files as above, you will also need to regenerate the workflow files based on the latest `qhub` version's templates.

With the newly upgraded `qhub-config.yaml` file, run:

```shell
qhub render -c qhub-config.yaml
```

(Note that `qhub deploy` would perform this render step too, but will also immediately redeploy your QHub.)

Commit all the files (`qhub-config.yaml` and GitHub/GitLab workflow files) back to the remote repo. All files need to be committed together in the same commit.
