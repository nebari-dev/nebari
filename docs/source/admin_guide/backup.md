# Manual backups

Manual backups requires amount to:

- Tarballing the /home directory
- Saving to block storage [s3, google cloud storage, etc]
- Downloading and untaring to new cluster

This specific guide shows how to do this on a cluster on AWS.

## Pre-requisites

- [Install kubectl](<https://kubernetes.io/docs/tasks/tools/>)
- [Install AWS command-line tool](<https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html>)

## Kubectl configuration

To setup kubectl, obtain the name of the cluster. If the user knows the deployment region of the current cluster, this is straightforward:

```shell
aws eks list-clusters --region=us-west-2
```

Copy the relevant name from this output, and run this command:

```shell
aws eks update-kubeconfig  --region us-west-2 --name <relevant-name>
```

## Pod deployment

With kubectl configured, the user now needs to deploy the pod that allows the user to access the cluster files. First save the follow pod specification to a file named `pod.yaml`

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
        claimName: "<mount-share-drive>"
  containers:
    - name: debugger
      image: ubuntu
      command: ["sleep", "36000"]
      volumeMounts:
        - mountPath: "/data"
          name: volume-to-debug-ubuntu
```

To determine what should replace `<mount-share-drive>` run `kubectl get pvc -n dev`. This is the volume that doesn't has conda in the name, and has the same storage space as specified by the `shared<sub>filesystem</sub>` line in `qhub-config.yaml`. In the example the name is `nfs-mount-dev-share`

With the name of the nfs volume saved in the file, run:

```shell
kubectl apply -f pod.yaml -n dev
```

If you have a namespace other than the default dev, replace `dev` with your namespace. To get a shell to this running pod, run:

```shell
kubectl exec -n dev --stdin --tty volume-debugger-ubuntu -- /bin/bash
```

Again replacing the `dev` namespace as needed.

## Installations

The user must install several `apt` packages, as the pod spun up is a basic pod. The following commands installs them:

```shell
apt update
apt install curl -y
apt install unzip -y
```

Because the user is on AWS, the AWS command-line tool is also installed.:

```shell
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
aws configure
```

The last command from preceding prompts for your AWS public/private key, and default region. Past each of these and press enter. To ignore and skip the output, press enter.

## Backups

To backup the file system, run:

```shell
cd /data
tar -cvf <custom_name>.tar /home
```

The preferred naming scheme includes a year-month-day, example `2021-04-23<sub>home</sub><sub>backup.tar</sub>`. The user can utilize multi-backups through this step. This step takes several minutes depending on the size of the home directories.

## Upload to block storage

Once this is complete, the user uploads the tar file to S3 using the AWS command-line tool:

```shell
aws s3 cp 2021-04-23.tar s3://<your_bucket_name>/backups/2021-04-23.tar
```

Replacing your <your<sub>bucket</sub><sub>name</sub>> with a bucket you have created. If you don't have an existing bucket, instructions are here:
<https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html>

## Download from block storage and decompress

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

## Google cloud provider

To use the Google Cloud provider, install [gsutil](https://cloud.google.com/storage/docs/gsutil_install). The instructions are same as the preceding steps. Additionally, use these commands for copy/download of the backup:

```shell
cd /data
gsutil cp 2021-04-23.tar gs://<your_bucket_name>/backups/2021-04-23.tar

cd /data
gsutil cp gs://<your_bucket_name>/backups/2021-04-23.tar .
```

## Digital Ocean

Similar instructions, but use Digital Ocean spaces. This guide explains installation of the command-line tool:
https://www.digitalocean.com/community/tutorials/how-to-migrate-from-amazon-s3-to-digitalocean-spaces-with-rclone
