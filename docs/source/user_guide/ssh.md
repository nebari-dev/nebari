# SSH/SFTP Access

QHub provides a secure method for users to login while also providing additional
ways to connect to the cluster through
[`jupyterhub-ssh`](https://github.com/yuvipanda/jupyterhub-ssh).
This allows users to access a cluster and a JupyterLab environment via
[`ssh`](https://en.wikipedia.org/wiki/Secure_Shell). In addition, users
can easily transfer files back and forth via
[`sftp`](https://en.wikipedia.org/wiki/SSH_File_Transfer_Protocol).
And for users who prefer terminal based editors, such as emacs or vim, they
can log in and automate tasks on the cluster without browser access. 
For more detailed information on using `jupyterhub-ssh`, please refer to the
[documentation](https://jupyterhub-ssh.readthedocs.io/en/latest/index.html).

In order to login via `ssh` a user needs to generate an API token. Visit
`https://<qhub-url>/hub/token`. Where `<qhub-url>` is the domain name of
your QHub cluster. You will be shown a screen similar to the one below. 
You need only generate the API token once; it can be reused going forward. 
To revoke the API token, simply return to this page and click `revoke`.

![qhub api token](../images/qhub_api_token.png)

To request a new token, add a short description, such as
`ssh login token`, and click on `Request new API token`. 
Copy and save the generated api token (in this case `f0b80688484a4ac79a21b38ec277ca08`).

![qhub api token generated](../images/qhub_api_token_generated.png)

You can now log into the QHub cluster via the terminal using `ssh`. Note 
that you will use your QHub username, shown in the top right-hand corner of 
the screen. You will need to provide this username explicitly when connecting 
via `ssh`.  See the example below on using the `-o` option with `ssh`, and notice 
the ports used by QHub for `ssh` and `sftp`.

> - `ssh` uses port `8022`
> - `sftp` uses port `8023`

```
$ ssh -o User=costrouchov@quansight.com training.qhub.dev -p 8022
The authenticity of host '[training.qhub.dev]:8022 ([35.223.107.201]:8022)' can't be established.
RSA key fingerprint is SHA256:mKy546LpI0cbqm/IY8dQR0B5QcbEziWLjLglern5G+U.
This key isn't known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '[training.qhub.dev]:8022' (RSA) to the list of known hosts.
(costrouchov@quansight.com@training.qhub.dev) Password:
costrouchov@quansight.com@jupyter-costrouchov-40quansight-2ecom:~$
```
