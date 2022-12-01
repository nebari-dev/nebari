# Preemptible and Spot instances on QHub

A preemptible or spot VM is an instance that you can create and run at a much lower price than normal instances. Azure
and Google Cloud platform use the term preemptible, while AWS uses the term spot, and Digital Ocean doesn't support
these types of instances. However, the cloud provider might stop these instances if it requires access to those
resources for other tasks. Preemptible instances are excess Cloud Provider's capacity, so their availability varies with
usage.

## Usage

### Google Cloud Platform

The `preemptible` flag in the QHub config file defines the preemptible instances.

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

Spot instances aren't supported at this moment.

### Azure

Preemptible instances aren't supported at this moment.

### Digital Ocean

Digital Ocean doesn't support these type of instances.
