# Preemptible and Spot Instances on QHub

A preemptible or spot VM is an instance that you can create and run at
a much lower price than normal instances. Azure and GCP use the term
preemptible, AWS uses the term spot, and Digital Ocean does not
support these types of instances. However, the cloud provider might
stop these instances if it requires access to those resources for
other tasks. Preemptible instances are excess Cloud Provider's
capacity, so their availability varies with usage. 

## Usage

### Google Cloud Platform

Preemptible instances can be defined via using the `preemptible` flag
in the QHub config file as following.


```yaml
google_cloud_platform:
  project: project-name
  region: us-central1
  zone: us-central1-c
  availability_zones:
  - us-central1-c
  kubernetes_version: 1.18.16-gke.502
  node_groups:
# ...
    preemptible-instance-group:
      preemptible: true
      instance: "e2-standard-8"
      min_nodes: 0
      max_nodes: 10
```

### Amazon Web Services

Spot instances are not supported at this moment.

### Azure

Preemptible instances are not supported at this moment.

### Digital Ocean

Digital Ocean does not support these type of instances.
