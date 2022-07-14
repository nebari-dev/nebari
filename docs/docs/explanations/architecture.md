---
id: infrastructure-architecture
title: Nebari architecture and conceptual guide
---

# Nebari architecture and conceptual guide

Below are diagrams to help show the architecture and design behind
Nebari. The diagrams are meant to show different levels. There are
cloud specific infrastructure diagrams along with a single diagram to
outline the Kubernetes services.

## Infrastructure

### Digital Ocean (DO)

The Digital Ocean deployment is the simplest of the cloud
providers. We deploy a managed Kubernetes not within a virtual
network. Similar to all other deployments auto-scaling is enabled. A
limitation of Digital Ocean auto-scaling is that it only scales down
to one. Once Nebari is fully deployed a load-balancer is connected to
the Kubernetes cluster through [Traefik](https://traefik.io/).

### Amazon Web Services (AWS)

![AWS Architecture Diagram](/img/architecture-diagram-aws.png)

AWS is the most complex of the cloud deployments with significant
effort being put into networking. An EKS managed kubernetes cluster is
deployed within a given region. A restriction of AWS eks is that it
must be deployed within two subnets in a region. Nebari supports spot
instances, auto-scaling to zero, and GPU instances.

### Google Cloud Platform (GCP)

![GCP Architecture Diagram](/img/architecture-diagram-gcp.png)

### Azure

![Azure Architecture Diagram](/img/architecture-diagram-azure.png)

## Kubernetes services

![Kubernetes Architecture Diagram](/img/architecture-diagram-kubernetes.png)

The most significant effort in Nebari is deploying the services within
the Kubernetes cluster. All of the infrastructure diagrams before 
