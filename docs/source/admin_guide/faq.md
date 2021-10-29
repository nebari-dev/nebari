# Frequently Asked Questions

## On AWS, why do user instances occasionally die ~30 minutes after spinning up a large dask cluster?

AWS uses Amazon's Elastic Kubernetes Service (EKS) for hosting the
kubernetes cluster. [EKS requires the use of at least two availability zones](https://docs.aws.amazon.com/eks/latest/userguide/infrastructure-security.html). The
QHub cluster has an
[autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html)
that has a default service that automatically balances the number of
EC2 instances between the two availability zones. When larger dask
clusters are created and destroyed, occasionally the autoscaler will
attempt to reschedule a user pod in the other availability zone. When
this happens, Kubernetes doesn't successfully transfer the active pod
to the other zone and the pod dies.

To stop this occuring, the autoscaler service "AZRebalance" needs to
be manually suspended. Currently this autoscaler service is not managed
by terraform. Disabling it via the console will be permanent for the
life of the cluster. [There is an open issue to permanently fix this via
terraform](https://github.com/Quansight/qhub/issues/786)

To disable the AZRebalance service, follow the steps in this [AWS
documentation](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-suspend-resume-processes.html)
to suspend the AZRebalance service.

## Can I deploy an arbitrary pod?

Yes, add extensions as follows:

```
extensions:
  - name: echo-test
    image: inanimate/echo-server:latest
    urlslug: echo
    private: true
```

This will deploy a simple service based on the image provided. name must be a simple terraform-friendly string.

It will be available on your QHub site at the /echo URL (or whatever urlslug you provide). Users will be required to be logged in if private is true.
