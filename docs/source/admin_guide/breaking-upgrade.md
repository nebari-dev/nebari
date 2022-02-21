# Upgrade - Redeployment for Breaking Changes

For versions that are known to require redeployment when upgrading, the steps for upgrade include:

- Back up user data by following [this guide](./backup.md).
- Change existing cluster to a different URL (e.g. `qhub-old.mycompany.com`) so it is hidden.
- Run `qhub upgrade` to make recommended modifications to the `qhub-config.yaml` file.
- Deploy a new QHub with the desired version (to your original preferred URL e.g. `qhub.mycompany.com` but a new project_name to avoid resource name clashes).
- Restore user data to the new cluster.
- Destroy old cluster when happy.

Please always check release notes for more details - and in all cases, backup your data before upgrading.

**The rest of this guide assumes you are upgrading from version v0.3.14 to v0.4.**

You may be deploying QHub based on a local configuration file, or you may be using CI/CD workflows in GitHub or GitLab. Either way, you will need to locate a copy of your `qhub-config.yaml` configuration file to upgrade it (and commit back to your git repo in the CI/CD case).

For CI/CD deployments, you will need to `git clone <repo URL>` into a folder on your local machine if you haven't done so already.

## 1. Backup existing data

Perform manual backups of the NFS data and JupyterHub database (ignore the section about Keycloak data since that will not exist in your v0.3.14 cluster).

The [Manual Backup guide is here](./backup.md).

## 2. Rename existing QHub URL

This will allow the existing cluster to remain alive in case it is needed, but the idea would be not to have it in use from now on.

In the qhub-config.yaml for example:

```
project_name: myqhub
domain: qhub.myproj.com
```

could become:

```
project_name: myqhub
domain: qhub-old.myproj.com
```

Run qhub deploy using the existing (old) version of qhub.

## 3. Upgrade the `qhub` command package

To install (or upgrade) your pip installation of the Python package used to manage QHub:

```shell
pip install --upgrade qhub==0.4.0
```

## 4. Upgrade `qhub-config.yaml` file

Now we need to go back to the original `qhub-config.yaml` file which contained the original domain.

In the folder containing your QHub configuration file, run:

```shell
qhub upgrade -c qhub-config.yaml
```

This will output a newer version of `qhub-config.yaml` that's compatible with the new version of `qhub`. The process outputs a list of changes it has made.

The `upgrade` command creates a copy of the original unmodified config file (`qhub-config.yaml.old.backup`) as well as a JSON file (`qhub-users-import.json`) used to import existing users into Keycloak.

## 5. Rename the Project and Increase Kubernetes version

You need to rename the project to avoid clashes with the existing (old) cluster which would otherwise already own resources based on the names that the new cluster will attempt to use.

The domain should remain as the preferred main one that was always in use previously.

For example:

```
project_name: myqhub
domain: qhub.myproj.com
```

could become:

```
project_name: myqhubnew
domain: qhub.myproj.com
```

> It is also a good time to upgrade your version of Kubernetes. Look for the `kubernetes_version` field within the cloud provider section of the `qhub-config.yaml` file and increase it to the latest.

## 6. Redeploy QHub

You will now have a `qhub-config.yaml` file that you can deploy.

```shell
qhub deploy -c qhub-config.yaml
```

At this point you will see an error message saying that deployment is prevented due to the `prevent_deploy` setting in your YAML file. This is a safeguard to ensure that you only proceed if you are aware of possible breaking changes in the current upgrade.

Because you are reading this guide, you already know that you needed to backup your data - see above again, if not. So you can edit your `qhub-config.yaml`, find the line reading `prevent_deploy: true` and remove it.

Attempt the `qhub deploy -c qhub-config.yaml` command again and it should get further this time.

## 7. CI/CD: render and commit to git

For CI/CD (GitHub/GitLab) workflows, then as well as generating the updated `qhub-config.yaml` files as above, you will also need to regenerate the workflow files based on the latest `qhub` version's templates.

With the newly upgraded `qhub-config.yaml` file, run:

```shell
qhub render -c qhub-config.yaml
```

(Note that `qhub deploy` would have performed this render step too, but will also immediately redeploy your QHub. Run the render command alone if you are now working separately in your repo and don't want to redeploy.)

Commit all the files (`qhub-config.yaml` and GitHub/GitLab workflow files) back to the remote repo. All files need to be committed together in the same commit.

## 8. Update OAuth callback URL for Auth0 or GitHub

If your QHub deployment relies on Auth0 or GitHub for authentication, please update the OAuth callback URL.

<details><summary>Click for more detailed instructions </summary>

1. Navigate to the your Auth0 tenacy homepage and from there select "Applications".

2. Select the "Regular Web Application" with the name of your deployment.

3. Under the "Application URIs" section, paste the new OAuth callback URL in the "Allowed Callback URLs" text block.
- The URL will take the shape:
    ```
    https://{your-qhub-domain}/auth/realms/qhub/broker/auth0/endpoint
    ```

Updating the GitHub Application instead is very similar, but the OAuth callback will be at `https://{your-qhub-domain}/auth/realms/qhub/broker/github/endpoint`

</details>

## 9. Restore from Backups

Next, return to the [Manual Backups documentation](./backup.md) to perform:

1. Restore the NFS data from your S3 (or similar) backup
2. Immediately after restoring NFS data, you must run the command `chown -R 1000:100 /data/home` as explained in the backup/restore docs for v0.4 upgrades.
3. Restore the JupyterHub sqlite database.

## 10. Import users into Keycloak

The last two steps are to:

1. Change the Keycloak `root` user password, documented [here](../installation/login.md#change-keycloak-root-password) and
2. Import existing users, documented [here](../admin_guide/backup.md#import-keycloak).

For more details on this process, visit the [Keycloak docs section](../installation/login.md).


## Known versions that require re-deployment

Version `v0.3.11` on AWS has an error with the kubernetes config map. See [this discussion](https://github.com/Quansight/qhub/discussions/841) for more details.

Version `v0.4`.
