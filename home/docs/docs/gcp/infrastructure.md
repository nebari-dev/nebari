# Base Cost

The cluster has been preconfigured with cost in mind. We would like to
minimize cost when the cluster is not in use while providing the
ability to scale up.

Google Cloud also provides a compelling offering for QHub. Since May
2020 they started charging a base rate of \$70/month for each running
kubernetes cluster. However, they make up for the fact with their
great support for auto-scaling groups. They are the only provider to
support auto-scaling a nodegroup to 0 workers at the moment.

The default provisioned setup used `n1-standard-2` which cost around \$40/month.

- general pool :: min 1 $40 <-> max 1 $40
- user pool :: min 0 <-> max 4 \$160
- worker pool :: min 0 <-> max 5 \$200

TODO: talk about cost of storage and load balancer (not yet
investigated).

# Autoscaling

Google cloud has the best support for auto scaling groups. Most
importantly they support scaling down to 0 nodes for a given
nodegroup.
