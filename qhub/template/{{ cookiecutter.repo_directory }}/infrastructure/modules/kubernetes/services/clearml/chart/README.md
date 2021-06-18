# ClearML Server for Kubernetes Clusters Using Helm
# Cloud Ready Version (Advanced)
##  Auto-Magical Experiment Manager & Version Control for AI

[![GitHub license](https://img.shields.io/badge/license-SSPL-green.svg)](https://img.shields.io/badge/license-SSPL-green.svg)
[![GitHub version](https://img.shields.io/github/release-pre/allegroai/clearml-server.svg)](https://img.shields.io/github/release-pre/allegroai/clearml-server.svg)
[![PyPI status](https://img.shields.io/badge/status-beta-yellow.svg)](https://img.shields.io/badge/status-beta-yellow.svg)

## Introduction

The **clearml-server** is the backend service infrastructure for [ClearML](https://github.com/allegroai/clearml).
It allows multiple users to collaborate and manage their experiments.
By default, *ClearML is set up to work with the ClearML Demo Server, which is open to anyone and resets periodically. 
In order to host your own server, you will need to install **clearml-server** and point ClearML to it.

**clearml-server** contains the following components:

* The ClearML Web-App, a single-page UI for experiment management and browsing
* RESTful API for:
    * Documenting and logging experiment information, statistics and results
    * Querying experiments history, logs and results
* Locally-hosted file server for storing images and models making them easily accessible using the Web-App

Use this repository to add **clearml-server** to your Helm and then deploy **clearml-server** on Kubernetes clusters using Helm.

## Deploying Your Own Elasticsearch, Redis and Mongodb

ClearML Server requires that you have elasticsearch, redis and mongodb services.
This chart default templates contains [bitnami](https://bitnami.com/) charts for [redis](https://github.com/bitnami/charts/tree/master/bitnami/redis) and [mongodb](https://github.com/bitnami/charts/tree/master/bitnami/mongodb), and the official chart for elasticsearch (which is currently still beta).
You can either use the default ones, or use your own deployments and set their name and ports in the appropriate sections of this chart.
In order to use your own deployment, make sure to disable the existing one in the `values.yaml` (for example, in order to disable elastic set `elasticsearch.enabled = false`) 

## Prerequisites

1. a Kubernetes cluster
1. Persistent Volumes for `pvc-apiserver.yaml`, `pvc-fileserver.yaml`, and `pvc-agentservices.yaml`.
1. Persistent volumes for elasticsearch, mongodb and redis (redis is optional). 
   See relevant information for each chart:
   * [elasticsearch](https://github.com/elastic/helm-charts/blob/7.6.2/elasticsearch/values.yaml)
   * [mongodb](https://github.com/bitnami/charts/tree/master/bitnami/mongodb#parameters)
   * [redis](https://github.com/bitnami/charts/tree/master/bitnami/redis#parameters)
   Make sure to define the following values for each PV: 
   * elasticsearch - in the `values.yaml` set `elasticsearch.persistence.enabled=true` and set `elasticsearch.volumeClaimTemplate.storageClassName` to the storageClassName used in your elasticsearch PV.
   * mongodb - in order to define a persistent volume for mongodb, in the `values.yaml` set `mongodb.persistence.enabled=true` and set `mongodb.persistence.storageClass` to the storageClassName used in your mongodb PV.
     Read [here](https://github.com/bitnami/charts/tree/master/bitnami/mongodb#parameters) for more details.
   * redis - in order to define a persistent volume for redis, in the `values.yaml` set `redis.master.persistence.enabled=true` and set `redis.master.persistence.storageClass` to the storageClassName used in your redis PV.
     Read [here](https://github.com/bitnami/charts/tree/master/bitnami/redis#parameters) for more details.
1. `kubectl` is installed and configured (see [Install and Set Up kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) in the Kubernetes documentation)
1. `helm` installed (see [Installing Helm](https://helm.sh/docs/using_helm/#installing-helm) in the Helm documentation)

## Deploying ClearML Server in Kubernetes Clusters Using Helm 
 
1. Add the **clearml-server** repository to your Helm:

        helm repo add allegroai https://allegroai.github.io/clearml-server-helm-cloud-ready/

1. Confirm the **clearml-server** repository is now in Helm:

        helm search repo clearml

    The helm search results must include `allegroai/clearml-server-cloud-ready`.

1. Install `clearml-server-cloud-ready` on your cluster:

        helm install clearml-server allegroai/clearml-server-cloud-ready --namespace=clearml --create-namespace

    A  clearml `namespace` is created in your cluster and **clearml-server** is deployed in it.
   
        
## Updating ClearML Server application using Helm

1. If you are upgrading from the [single node version](https://github.com/allegroai/clearml-server-helm) of ClearML Server helm charts, follow these steps first:

    1. Log in to the node previously labeled as `app=trains`
    1. Copy each folder under /opt/clearml/data to it's persistent volume. 
    1. Follow the [Deploying ClearML Server](##-Deploying-ClearML-Server-in-Kubernetes-Clusters-Using-Helm) instructions to deploy Clearml

1. Update using new or updated `values.yaml`
        
        helm upgrade clearml-server allegroai/clearml-server-cloud-ready -f new-values.yaml
        
1. If there are no breaking changes, you can update your deployment to match repository version:

        helm upgrade clearml-server allegroai/clearml-server-cloud-ready
   
   **Important**: 
        
    * If you previously deployed a **clearml-server**, you may encounter errors. If so, you must first delete old deployment using the following command:
    
            helm delete --purge clearml-server
            
        After running the `helm delete` command, you can run the `helm install` command.
        
## Port Mapping

After **clearml-server** is deployed, the services expose the following node ports:

* API server on `30008`
* Web server on `30080`
* File server on `30081`

## Accessing ClearML Server

Access **clearml-server** by creating a load balancer and domain name with records pointing to the load balancer.

Once you have a load balancer and domain name set up, follow these steps to configure access to clearml-server on your k8s cluster:

1. Create domain records

   * Create 3 records to be used for Web-App, File server and API access using the following rules: 
     * `app.<your domain name>` 
     * `files.<your domain name>`
     * `api.<your domain name>`
     
     (*for example, `app.clearml.mydomainname.com`, `files.clearml.mydomainname.com` and `api.clearml.mydomainname.com`*)
2. Point the records you created to the load balancer
3. Configure the load balancer to redirect traffic coming from the records you created:
     * `app.<your domain name>` should be redirected to k8s cluster nodes on port `30080`
     * `files.<your domain name>` should be redirected to k8s cluster nodes on port `30081`
     * `api.<your domain name>` should be redirected to k8s cluster nodes on port `30008`

## Additional Configuration for ClearML Server

You can also configure the **clearml-server** for:
 
* fixed users (users with credentials)
* non-responsive experiment watchdog settings
 
For detailed instructions, see the [Optional Configuration](https://github.com/allegroai/clearml-server#optional-configuration) section in the **clearml-server** repository README file.
