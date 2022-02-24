# Manual backups

Your cloud provider may have native ways to backup your Kubernetes cluster and volumes.

This guide describes how you would manually obtain the data you need to repopulate your QHub if your cluster is lost and you wish to start it up again from the `qhub-config.yaml` file.

There are three main locations that you need to backup:

1. The Network File System (NFS) volume where all JupyterLab workspace files are stored
2. The JupyterHub database (for Dashboard configuration)
3. The Keycloak user/group database

## Network file system

This amounts to:

- Tarballing the /home directory
- Saving to block storage [s3, google cloud storage, etc]
- Downloading and untaring to new cluster

This specific guide shows how to do this on an AWS cluster and upload to AWS S3.

### Pre-requisites

- [Install kubectl](<https://kubernetes.io/docs/tasks/tools/>)
- [Install AWS command-line tool](<https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html>)

### Kubectl configuration

To setup kubectl, obtain the name of the cluster. If the user knows the deployment region of the current cluster, this is straightforward:

```shell
aws eks list-clusters --region=us-west-2
```

Copy the relevant name from this output, and run this command:

```shell
aws eks update-kubeconfig  --region us-west-2 --name <relevant-name>
```

### Pod deployment

With `kubectl` configured,  the next step will be to deploy the pod that allows the user to access the cluster files. First, save the following pod specification to a file named `pod.yaml`:

```yaml
kind: Pod
apiVersion: v1
metadata:
  name: volume-debugger-ubuntu
  namespace: dev
spec:
  volumes:
    - name: volume-to-debug-ubuntu
      persistentVolumeClaim:
        claimName: "jupyterhub-dev-share"
  containers:
    - name: debugger
      image: ubuntu
      command: ["sleep", "36000"]
      volumeMounts:
        - mountPath: "/data"
          name: volume-to-debug-ubuntu
```

> Note in QHub versions before v0.4 replace `claimName: "jupyterhub-dev-share"` with `claimName: "nfs-mount-dev-share"`

Once the file `pod.yml` has been created, run the following command:

```shell
kubectl apply -f pod.yaml -n dev
```

If you have a namespace other than the default dev, replace `dev` with your namespace. To get a shell to this running pod, run:

```shell
kubectl exec -n dev --stdin --tty volume-debugger-ubuntu -- /bin/bash
```

Again replacing the `dev` namespace as needed.

### Installations

The user must install several `apt` packages, as the pod spun up is a basic pod. The following commands installs them:

```shell
apt update
apt install curl -y
apt install unzip -y
```

Because the user is on AWS, the AWS command-line tool is also installed:

```shell
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
aws configure
```

The last line in the command above prompts for your AWS public/private key and default region. Paste each of these and press enter. To ignore and skip the output, press enter.

### Backups

To backup the file system, run:

```shell
cd /data
tar -cvf <custom_name>.tar .
```

The preferred naming scheme includes a year-month-day, example `2021-04-23_home_backup.tar`. The user can utilize multi-backups through this step. This step takes several minutes depending on the size of the home directories.

### Upload to block storage

Once this is complete, the user uploads the tar file to S3 using the AWS command-line tool:

```shell
aws s3 cp 2021-04-23.tar s3://<your_bucket_name>/backups/2021-04-23.tar
```

Replacing `your_bucket_name` with a bucket you have created. If you don't have an existing bucket, instructions are here:
<https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html>

### Download from block storage and decompress

Now that the data backed up, perform the same steps preceding for the new cluster. This includes:

- Configuring kubectl for the new cluster.
- Creating a pod on the new cluster and getting shell access into it.
- Installing the apt packages.
- Configuring AWS.

Once AWS gets configured on the new pod, the user can then download the backup with:

```shell
cd /data
aws s3 cp s3://<your_bucket_name>/backups/2021-04-23.tar .
```

The last step is to extract the contents of the tarball:

```shell
cd /data
tar -xvf 2021-04-23.tar
```

The file permissions for the default tar is same as the original files.

> **Important: If upgrading from 0.3.14 or earlier to 0.4 or later**
>
> QHub v0.4: If restoring your NFS as part of the upgrade you must also run some extra commands, immediately after extracting from the tar file.
>
> Because previous versions contained the `shared` folder within `home`, but they are now both at the same level, you must run:
> ```shell
> cd /data
> cp -r home/shared/* shared/
> rm -rf home/shared/
> ```
> And then:
> ```shell
> chown -R 1000:100 /data/home/*
> chown -R 1000:100 /data/shared/*
> ```
> This is because all users have the same uid in QHub v0.4 onward.
>

### Google cloud provider

To use the Google Cloud provider, install the [gsutil](https://cloud.google.com/storage/docs/gsutil_install) CLI. The instructions are the same as the preceding steps. Additionally, use these commands for copy/download of the backup:

```shell
cd /data
gsutil cp 2021-04-23.tar gs://<your_bucket_name>/backups/2021-04-23.tar

cd /data
gsutil cp gs://<your_bucket_name>/backups/2021-04-23.tar .
```

### Digital Ocean

Similar instructions, but use Digital Ocean spaces. This guide explains installation of the command-line tool:
<https://www.digitalocean.com/community/tutorials/how-to-migrate-from-amazon-s3-to-digitalocean-spaces-with-rclone>


## JupyterHub Database

The JupyterHub database will mostly be recreated whenever you start a new cluster, but should be backed up to save Dashboard configurations.

You want to do something very similar to the NFS backup, above - this time you need to back up just one file located in the  PersistentVolume `hub-db-dir`.

First, you might think you can just make a new `pod.yaml` file, this time specifying `claimName: "hub-db-dir"` instead of `claimName: "jupyterhub-dev-share"`. However, `hub-db-dir` is 'Read Write Once' - the 'Once' meaning it can only be mounted to one pod at a time, but the JupyterHub pod will already have this mounted! So the same approach will not work here.

Instead of mounting to a new 'debugger pod' you have to access the JupyterHub pod directly using the `kubectl` CLI.

Look up the JupyterHub pod:
```bash
kubectl get pods -n dev
```

It will be something like `hub-765c9488d6-8z4nj`.

Get a shell into that pod:

```bash
kubectl exec -n dev --stdin --tty hub-765c9488d6-8z4nj -- /bin/bash
```

There is no need to TAR anything up since the only file required to be backed up is `/srv/jupyterhub/jupyterhub.sqlite`.

### Backing up JupyterHub DB

Now we just need to upload the file to S3. You might want to [install the AWS CLI tool](#installations) as we did before, but unfortunately the Hub container is quite locked down and it isn't straightforward to install that... So instead you need to upload to S3 using curl directly:

For more details please refer to the [using curl to access AWS S3 buckets](./awss3curl.md) documentation.

### Restoring JupyterHub DB

You will need to overwrite the file `/srv/jupyterhub/jupyterhub.sqlite` based on the version backed up to S3.

You should restart the pod:
```bash
kubectl delete -n dev pod hub-765c9488d6-8z4nj
```

As for uploads, [you may need to use curl to download items from an AWS S3 bucket](./awss3curl.md).

## Keycloak user/group database

QHub provides a simple script to export the important user/group database. Your new QHub cluster will recreate a lot of Keycloak config (including new Keycloak clients which will have new secrets), so only the high-level Group and User info is exported.

If you have a heavily customized Keycloak configuration, some details may be omitted in this export.

### Export Keycloak

The export script is at [`qhub/scripts/keycloak-export.py`](https://github.com/Quansight/qhub/blob/main/scripts/keycloak-export.py).

Locate your `qhub-config.yaml` file, for example by checking out of your Git repo for you QHub. Activate a virtual environment with the `qhub` Python package installed.

This assumes that the password visible in the `qhub-config.yaml` file under the `security.keycloak.initial_root_password` field is still valid for the root user.

If not, first set the `KEYCLOAK_ADMIN_PASSWORD` environment variable to the new value.

Run the following to create the export file:

```shell
python qhub/scripts/keycloak-export.py -c qhub-config.yaml > exported-keycloak.json
```

You may wish to upload the Keycloak export to the same S3 location where you uploaded the TAR file in the NFS section.

### Import Keycloak

To re-import your users and groups, [login to the /auth/ URL](../installation/login.md) using the root username and password.

Under 'Manage' on the left-hand side, click 'Import'. Locate the `exported-keycloak.json` file and select it. Then click the 'Import' button.

All users and groups should now be present in Keycloak. Note that the passwords will not have been restored so you may need to be reset them after this step.
