# Update/edit a Conda Virtual Environment

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

Commit the changes, and make a [PR](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request)
into a master branch. The update will take from 5 to 30 minutes to complete, depending on the environment's complexity. 
If after 30 minutes the new environment is still not available, check the latest log files from the user instance in the
`/home/conda/store/.logs` directory to troubleshoot.
