# Management

## Add users to QHub

One of the first things you might want to do is to **add new users**
to your QHub.

This can be done through the Keycloak web console. See [Adding a QHub user](file:///Users/dan/Dev/qhub/docs/build/source/installation/login.html#adding-a-qhub-user) for details.

## Upgrades and dependencies management

### Update/edit a Conda Virtual Environment

To update a current conda environment and redeploy you will need to:
* Create a new branch on your repository
* Make changes to the `qhub-config.yaml` file under the `environments` key.
> NOTE: in [YAML](https://yaml.org/spec/1.2/spec.html#mapping//),
  each level is a dictionary key, and every 2 white spaces represent values for those keys.

To add a new environment, add two spaces below the `environments` key such as the example below.
```yaml
environments:
  "example.yaml":
    name: example
    channels:
    - conda-forge
    dependencies:
    - python
    - pandas
```

Commit the changes, and make a
[PR](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request)
into a master branch. The update will take from 5 to 30 minutes to
complete, depending on the environment's complexity.  If after 30
minutes the new environment is still not available, check the latest
log files from the user instance in the `/home/conda/store/.logs`
directory to troubleshoot.

* Note that the current version will not notify you if an environment fails to solve. The only way to see failures is by manually checking the above logs.*

## Copy Files into Users' Home Folders

Within their own JupyterLab sessions, admins can add files to a folder
called `shared/.userskel`. Any files in there will be copied to a
user's own home folder whenever they start a new JupyterLab
session. Existing files with the same name will not be
overwritten. Admin users are defined as members of the admin group as
specified in your qhub-config.yaml file.

## Monitor your QHub deployment

TODO: add instruction on how to install and use K9s for monitoring the
system deployment.
