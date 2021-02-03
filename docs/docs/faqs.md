# Frequently Asked Questions (FAQ)

> ## Do you have a question about QHub that is not answered in the [documentation](https://qhub.dev)?
>
> + Head over to our [Discussion Q&A](https://github.com/Quansight/qhub/discussions/categories/q-a) page on GitHub and leave your question to our team.
> 
> Have feedback or would like to request improvements on the docs? Open an [issue](https://github.com/Quansight/qhub/issues/new/choose) and tell us more.
    

### Who was QHub made for?
In summary, anyone who would like to deploy using JupyterHub. From data scientists and researchers to DevOps engineers,
QHub was designed to abstract the complexities involved on using cloud services and parallel computing.

It introduces the concept of deployment from JupyterHub to a chosen Cloud provider using Kubernetes, without the need for 
a DevOps specialist. I.e., _Kubernetes for those who don't know how to use Kubernetes_. 

The aim is to make it easier for users to set up infrastructure that is ready to use, scalable, and stable, all with out-of-the-box solutions.
> QHub is also entirely customisable, although to properly adapt the default settings will require more in-depth DevOps knowledge.


## What is Infrastructure as Code and how is it related to QHub?
  
  + [Infrastructure as Code](https://docs.aws.amazon.com/whitepapers/latest/introduction-devops-aws/infrastructure-as-code.html) (IaC)
    is a system that handles the management of infrastructure (networks, virtual machines, load balancers, and connection
    topology) using the same versioning that DevOps teams use for source-code. Infrastructure as Code enables DevOps teams to test applications in production-like environments early in the development cycle.
  
    QHub brings together these concepts and tools in its architecture to provide users with the necessary infrastructure to perform development and deployments at scale without having to manually configure it themselves.


## Q: How do I retrieve my user data from the EFS Share before I destroy my QHub on AWS?
Answered by [@jkellndorfer](https://github.com/jkellndorfer).

We want to back up the user-data from the AWS EFS persistent volume associated with our QHub before we destroy it.
A possible avenue are the following steps:

1. Login to the AWS console
2. Determine which VPC (Virtual Private Cloud) your QHub EKS cluster is using.
3. From EFS find the cluster which used EFS Share and determine its ID, e.g. `fs-9083c231`.
3. Launch an AWS instance with Amazon Linux as the operating system.
   - Choose the same VPC from Step 2.
   - In `security groups` assure rights to NFS and SSH.
4. Login to the AWS instance.
5. Install EFS mount helper and mount the share (Instructions [here](https://docs.aws.amazon.com/efs/latest/ug/mounting-fs-mount-helper.html#mounting-fs-mount-helper-ec2) and [here](https://docs.aws.amazon.com/efs/latest/ug/mounting-fs-mount-helper.html#mounting-fs-mount-helper-ec2)). 

        sudo yum install -y nfs-utils
        sudo yum install -y amazon-efs-utils
        sudo mkdir /mnt/efs
        sudo mount -t efs fs-9261c667:/ /mnt/efs
        aws configure --profile efs_backup.  # enter your AWS KEY and SECRET_KEY WITH write rights to the backup bucket you want to use
     
6. Assume you mounted the EFS share on mountpoint `/mnt/efs`
        
        aws s3 cp --profile efs_backup --recursive /mnt/efs/home s3://<my-backup-bucket>/<my-backup-Prefix>
        
7. Terminate your EC2 AWS Linux instance.



## Q: How do I destroy my QHub deployment on Amazon AWS?
Answered by: [@jkellndorfer](https://github.com/jkellndorfer).

Follow the steps:

1. On your local QHub repo type the code snipped below:
```bash
  cd <your-qhub-repo>
  git pull              # to fetch the latest changes 
  cd infrastructure
  terraform destroy
```
2. If `terraform destroy` does not complete and stops with an `unauthorized` error, you should try running it a
second or several more times until you are stuck at the same `module`.

3. Then try to manually remove the "offending" module with
    ```
      terraform state rm <module>
    ```
    Followed (again) by
    ```bash
      terraform destroy
    ```
4. Repeat the above process for every module where the destroy process fails.
5. Finally, login to your AWS console and look for everything related to the EKS, LoadBalancer, database tables,
   autoscaling groups, node groups, EFS, volumes, IAM, etc. that may still be left and remove it.


## Q: How do I use `nbconvert --execute` on QHub from the Command Line?
Answered by: [@jkellndorfer](https://github.com/jkellndorfer).

Assume the notebook `my-notebook.ipynb` uses the environment `myenv`.

1. Activate the environment used in the notebook

        conda activate myenv

2. Check that the environment is part of the string returned by `jupyter kernelspec list`

        jupyter kernelspec list
        python3    /home/conda/store/802e4196e4af0f9dbc000362cdb3bfde2df34aa9512bcfa6511c384ccef4518f-myenv/share/jupyter/kernels/python3
      
Interestingly, the kernel name is "python3", but contains,  ...-myenv/share ..., so we are ok.

3. Convert the notebook using the `python3` label:

        jupyter nbconvert --ExecutePreprocessor.kernel_name=python3 --execute --to html my-notebook.ipynb
      
You should get a `my-notebook.html` file that was executed with the myenv kernel. 

## How do I update/edit a conda environment?
To update your current conda environment and redeploy you will need to:
* Create a new branch on your repository
* Make changes to the `qhub-config.yaml` file under the `environments` key.
> NOTE: in [YAML](https://yaml.org/spec/1.2/spec.html#mapping//),
  each level is a dictionary key, and every 2 white spaces represent values for those keys.
  
TO add a new environment, add two spaces below the `environments` key such as the example below.
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



## What is QHub?

  + QHub is an integrated data science environment designed and developed by scientists at [Quansight](https://www.quansight.com/). It enables teams to build and maintain a cost effective and scalable compute/data science platform in the cloud.


## What are the main benefits of using QHub?

  + QHub enables users to deliver stable environments rapidly and at scale. It allows teams enforce consistency by representing the desired state of their environments via code. QHub as a Infrastructure as Code platform prevents runtime issues caused by missing dependencies or configuration drifts.

## Is QHub free?

  + QHub is an open source project and free to use. However, the cloud service providers (Amazon Web Services, Google Cloud Platform, Digital Ocean) accessed through QHub require your personal service account information. Any paid services these providers offer and you choose to use for your projects will not be free.

## What challenges does QHub solve?

  + QHub aims to provide a smooth computing experience for teams of data scientists, engineers, educators, among others. For this, it abstracts away the complex details of deployment environments and management of infrastructure, making your configurations reproducible and your applications scalable.

## What technologies does QHub rely on?

  + QHub is built upon [JupyterHub](https://jupyterhub.readthedocs.io/en/stable/) and extends JupyterHub's capabilities to a much larger scale that is not possible to achieve using JupyterHub only. QHub comes with [Dask](https://dask.org/) integrated into it. Currently, QHub can be used with the three of the most popular cloud services, Amazon Web Services (AWS), Google Cloud Platform (GCP), and Digital Ocean (DO). For more details about the technologies QHub uses, please see [QHub's Technology Stack](https://qhub.readthedocs.io/en/latest/index.html) in the documentation.

## What is Jupyter Notebook?

  + Created by the nonprofit organization [Project Jupyter](https://jupyter.org/), the Jupyter Notebook is an open source web application that allows users to create and share documents that contain live code, equations, visualizations and narrative text on their browsers. See [Jupyter Notebook documentation](https://jupyter-notebook.readthedocs.io/en/stable/) for details.

## What is JupyterHub?

  + JupyterHub is a multi-user hub that spawns, manages, and proxies multiple instances of the single-user Jupyter notebook server that QHub is built upon. See [JupyterHub documentation](https://jupyterhub.readthedocs.io/en/stable/) for details.

## QHub vs JupyterHub**

  + JupyterHub is an excellent platform for shared computational environments. However, deploying and maintaining a scalable compute environment with JupyterHub is a significantly challenging task. QHub solves this problem by integrating Dask and the main components of cloud deployment into its architecture, providing a smooth experience of computation at scale on a single platform.

## What is Dask?

  + Dask is an open source library for parallel computing written in Python. It enables researchers to scale computations beyond the limits of their local machines. See [Dask documentation](https://docs.dask.org/en/latest/) for more details.


## What are environments?

  + A (programming) environment generally refers to a directory on your machine that contains a set of packages and dependencies to run your program or application. One might think of a programming environment similar to a namespace as defined in computer science/programming, which refers to an abstract container or environment created to hold a logical grouping of names.
  
    For different infrastructures, the term environment might be defined slightly differently. For example, a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) is a collection of conda packages that one’s program needs to work as desired. [Terraform](https://www.terraform.io/), which is an open source infrastructure as code software tool, defines an environment as “refer to the idea of having multiple distinct, named states associated with a single configuration directory” while a Dask environment is used often interchangeably with [configuration](https://docs.dask.org/en/latest/configuration.html).

## Why open source?

  + Open Source Software enables great advancements in science, and here at Quansight we advocate for the open source 
    community. QHub is only a single example how powerful open source software can be and how a combination of some of 
    the greatest open source tools can provide an invaluable service for those who are creating science.



  + Create an issue in the [Github repo](https://github.com/Quansight/qhub/issues/new/choose) to get answers from the 
    maintainers of QHub at Quansight.

