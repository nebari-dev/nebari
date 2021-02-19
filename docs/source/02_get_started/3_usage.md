# Usage

## Local Deployment

### Environment Variables
To deploy QHub set the environment variable `PYTHONPATH` and create a new sub-directory running:
```bash
export PYTHONPATH=$PWD:$PYTHONPATH
mkdir -p data
```

### Initialize configuration
Then, initialize the configuration file `qhub-config.yaml` with
```shell
python -m qhub init local --project=projectname --domain github-actions.qhub.dev --auth-provider=password --terraform-state=local
```

#### Generate user password
Each user on the `qhub-config.yaml` file will need a password. You can use [bcrypt](https://pypi.org/project/bcrypt/) to
generate a salted password by using the following python script:
```python
import bcrypt;

bcrypt.hashpw(b'<password>', bcrypt.gensalt())
```
Where `<password>` can be changed to any value.


TODO: describe this section with more precision. Where should the script be imported? Any exceptions for password characters?

### Render config file
Next, we will render the files from `qhub-config.yaml` running
```shell
python -m qhub render --config qhub-config.yaml -f
```

### Deploy modules

And finally, to deploy QHub:
```shell
python -m qhub deploy --config qhub-config.yaml --disable-prompt
```


To ease development we have already pointed the project's DNS record `jupyter.github-actions.qhub.dev` to the IP address 
`172.17.10.100`. TO make sure all is correctly set, check the load balancer IP address:
```shell
$ > load balancer ip command
```

In case the address does not correspond to `172.17.10.100`, point the DNS domain to the address by running
```ini
172.17.10.100 jupyter.github-actions.qhub.dev
```
### Verify deployment
Finally, if everything was set properly you should be able to cURL the JupyterHub server with
```shell
curl -k https://jupyter.github-actions.qhub.dev/hub/login
```

It is also possible to visit `https://jupyter.github-actions.qhub.dev` using the web browser.

### Cleanup
To clean up the installation use the command
```shell
python -m qhub destroy --config qhub-config.yaml 
```
Followed by 
```shell
minikube delete
```
The commands will delete all instances of QHub.

---

## Cloud Deployment

```shell
qhub init 
```