# Troubleshooting guide

## DNS domain=`your_qhub_domain` record does not exist

### Issue
During your initial QHub deployment, at the end of the `04-kubernetes-ingress` stage, you receive an output message stating that the DNS record for `your_qhub_domain` "appears not to exist, has recently been updated, or has yet to fully propagate."

### Reason for observed behavior
As the output message mentions, this is likely the result of the non-deterministic behavior of DNS.

Without going into a deep dive of what DNS is or how it works, the issue encountered here is that the when QHub tries to lookup the IP address associated with the DNS record, `your_qhub_domain`, nothing is returned. Unfortunately, this "lookup" is not as straight-forward as it sounds. To lookup the correct IP associated with this domain, many intermediate servers (root, top level domain, and authoritative nameservers) are checked, each with their own cache which was updated an unknown time ago (usually on the order of minutes but not always).

For those interested to learn more about DNS, see [this CloudFlare article](https://howdns.works/)).

### Troubleshooting
Again, as the output message mentions, it will ask if you want it to retry this DNS lookup again after another wait period; this wait period keeps increasing after each retry. However, it's still possible that after waiting 15 or more minutes that the DNS still won't resolve.

At this point, feel free to cancel the deployment and rerun the same deployment command again in an hour or two. Although not guaranteed, it's extremely likely that the DNS will resolve correctly after this prolonged wait period.


## A Conda-Store environment fails to build

### Issue
One of the two (`dashboard` or `dask`) Conda-Store environments created during the initial QHub deployment fails to appear as options when logged into JupyterHub.

If your user has access to Conda-Store, you can verify this by visiting `<your_qhub_domain>.com/conda-store` and having a look at the build status of the missing environment.

### Reason for observed behavior
The reason for this issue is due to how these environments are simultaneously built. Under the hood, Conda-Store relies on Mamba/Conda to resolve and download the specific packages listed in the environment YAML. If they both environment builds try to download the same package with different versions, the build that started first will have their package overwritten by the second build. This causes the first build to fail.

### Troubleshooting
To resolve this issue, navigate to `<your_qhub_domain>.com/conda-store`, find the environment build that failed and trigger it to re-build.
