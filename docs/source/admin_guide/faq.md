# Frequently asked questions

## On AWS, why do user instances occasionally die ~30 minutes after spinning up a large dask cluster?

AWS uses Amazon's Elastic Kubernetes Service for hosting the Kubernetes cluster.
[Elastic Kubernetes Service requires the use of at least two availability zones](https://docs.aws.amazon.com/eks/latest/userguide/infrastructure-security.html).
The QHub cluster has an [autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html) that has
a default service that automatically balances the number of EC2 instances between the two availability zones. When large
Dask clusters get initialized and destroyed, the autoscaler attempts to reschedule a user pod. This reschedule operation
occurs in the other availability zone. When this happens, Kubernetes doesn't successfully transfer the active pod to the
other zone and the pod dies.

To stop this occurring, the autoscaler service "AZRebalance" needs to be manually suspended. Currently this autoscaler
service isn't managed by terraform. Disabling it via the console is permanent for the life of the cluster.
[There is an open issue to permanently fix this via Terraform](https://github.com/Quansight/qhub/issues/786)

To turn off the AZRebalance service, follow the steps in this
[AWS documentation](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html) to suspend
the AZRebalance service.

To turn off the AZRebalance service, follow the steps in this
[AWS documentation](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html) to suspend
the AZRebalance service.

## Can a user deploy an arbitrary pod?

As a user, add extensions as follows:

```sh
extensions:
  - name: echo-test
    image: inanimate/echo-server:latest
    urlslug: echo
    private: true
```

This deploys a simple service based on the image provided. name must be a simple terraform-friendly string. It's
available on your QHub site at the `/echo` URL, or whatever URL slug you provide. Users need log-in credentials in if
the private is true.
