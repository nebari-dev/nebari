# Upgrade

Here we suppose a user would like to upgrade to a version
`<version>`, probably the latest full release of [QHub on PyPI](https://pypi.org/project/qhub/).

You may be deploying QHub based on a local configuration file, or you may be using CI/CD workflows in GitHub or GitLab. Either way, you will need to locate a copy of your qhub-config.yaml configuration file to upgrade it (and commit back to your git repo in the CI/CD case).

For CI/CD deployments, you will need to `git clone <repo URL>` into a folder on your local machine.

## Upgrade the qhub command package

To install (or upgrade) your pip installation of the Python package used to manage QHub:

```shell
pip install --upgrade qhub
```

The above will install the latest full version of qhub. For a specific older version use:

```shell
pip install --upgrade qhub==<version>
```

## Upgrade qhub-config.yaml file

In the folder containing your qhub configuration file, run:

```shell
qhub upgrade -c qhub-config.yaml
```

This will output a newer version of qhub-config.yaml that is compatible with the new version of qhub. The process will list any changes it has made. It will also tell you where it has stored a backup of the original file.

If you are deploying qhub from your local machine (i.e. not using CI/CD) then you will now have a qhub-config.yaml file that you can use to `qhub deploy -c qhub-config.yaml` through the latest version of the qhub command package.

## Special customizations

You may have made special customizations to your qhub config, such as using your own versions of Docker images. Please check your qhub-config.yaml and decide if you need to update any values that would not have been changed automatically - or, for example, you may need to build new versions of your custom Docker images to match any changes in QHub's images.

## Render and Commit to Git

For CI/CD (GitHub/GitLab) workflows, then as well as generating the updated qhub-config.yaml files as above, you will also need to regenerate the workflow files based on the latest qhub version's templates.

With the newly upgraded qhub-config.yaml file, run:

```shell
qhub render -c qhub-config.yaml
```

(Note that `qhub deploy` would perform this render step too, but will also immediately redeploy your qhub.)

Commit all the files (qhub-config.yaml and GitHub/GitLab workflow files) back to the remote repo. All files need to be committed together in the same commit.

## Known versions that require re-deployment

For versions that are known to error when upgrading, the steps for upgrade include:

- Deploy a new QHub with the desired version
- Back up user data and restore to the new cluster by following [this guide](https://docs.qhub.dev/en/stable/source/admin_guide/backup.html)
- Destroy old cluster

Version `v0.3.11` on AWS has an error with the kubernetes config map. See [this discussion](https://github.com/Quansight/qhub/discussions/841) for more details.
