# Manual Backups
This method for backing up and restoring requires amount to:

-   tarballing the /home directory
-   saving to block storage [s3, google cloud storage, etc]
-   downloading and untaring to new cluster

This specific guide will show how to do this on a cluster on AWS

## Pre-requisites

-   [Install kubectl](<https://kubernetes.io/docs/tasks/tools/>)
-   [Install AWS CLI](<https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html>)

## Kubectl configuration
To setup kubectl, first we must obtain the name of
the cluster. So long as you know the region your current cluster is
deployed in, this is straightforward:

    aws eks list-clusters --region=us-west-2

Copy the relevant name from this output, and run this command:

    aws eks update-kubeconfig  --region us-west-2 --name <relevant-name>

## Pod deployment

With kubectl configred, we now need to deploy the pod that will allow
us to access the cluster files. First save the follow pod spec to a
file named `pod.yaml`

    kind: Pod
    apiVersion: v1
    metadata:
      name: volume-debugger-ubuntu
      namespace: dev
    spec:
      volumes:
        - name: volume-to-debug-ubuntu
          persistentVolumeClaim:
           claimName: <mount-share-drive>
      containers:
        - name: debugger
          image: ubuntu
          command: ['sleep', '36000']
          volumeMounts:
    	- mountPath: "/data"
    	  name: volume-to-debug-ubuntu

To determine what should replace `<mount-share-drive>` run `kubectl
get pvc -n dev`. This will be the volume that doesn't have conda in
the name, and will have the same storage space as specified by the
`shared<sub>filesystem</sub>` line in `qhub-config.yaml`. In my example the name
is `nfs-mount-dev-share`

With the name of the nfs volume saved in the file, run:

    kubectl apply -f pod.yaml -n dev

If you have a namespace other than the default dev, replace `dev` with your namespace.

To get a shell to this running pod, run:

    kubectl exec -n dev --stdin --tty volume-debugger-ubuntu -- /bin/bash

Again replacing the `dev` namespace as needed.

## Installations

The pod we spun up is a basic pod, so several apt packages must be installed. The following commands will install them:

    apt update
    apt install curl -y
    apt install unzip -y

Because we are on aws, we will then install the AWS CLI:

    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    aws configure

The last command from above will prompt for your aws public/private
key, and default region. Past each of these and press enter. The
output can be ignored and skipped by pressing enter.

## Backups

The file system can now be backed up with the following:

    cd /data
    tar -cvf <custom_name>.tar /home

My preferred naming scheme includes a year-month-day,
e.g. `2021-04-23<sub>home</sub><sub>backup.tar</sub>`. This helps when multiple backups
are used. This step will take several minutes depending on the size of
the home directories.

\## Upload to block storage
Once this is complete, the AWS CLI can be used to upload the tar file to s3.

    aws s3 cp 2021-04-23.tar s3://<your_bucket_name>/backups/2021-04-23.tar

Replacing your <your<sub>bucket</sub><sub>name</sub>> with a bucket you have created. If
you don't have an existing bucket, instructions are here:
<https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html>

\## Download from block storage and decompress

Now that we have the data backed up,
perform the same steps above for the new cluster. This includes:

-   configuring kubectl for the new cluster
-   creating a pod on the new cluster and getting shell access into it
-   installing the apt packages
-   configuring AWS

Once AWS is configured on the new pod, we can then download the backup with:

    cd /data
    aws s3 cp s3://<your_bucket_name>/backups/2021-04-23.tar .

The last step is to extract the contents of the tarball:

    cd /data
    tar -xvf 2021-04-23.tar

By default tar will keep all of the same file permissions as the original files that were tarballed.

That's it! Enjoy.


## Google Cloud Provider

The same instructions as above, except install (gsutil)[https://cloud.google.com/storage/docs/gsutil_install) and use these commands for copy/download of the backup

    cd /data
    gsutil cp 2021-04-23.tar gs://<your_bucket_name>/backups/2021-04-23.tar

	cd /data
	gsutil cp gs://<your_bucket_name>/backups/2021-04-23.tar .
	
## Digital Ocean

Similar instructions, but use digital ocean spaces. This guide will explain installation: https://www.digitalocean.com/community/tutorials/how-to-migrate-from-amazon-s3-to-digitalocean-spaces-with-rclone
