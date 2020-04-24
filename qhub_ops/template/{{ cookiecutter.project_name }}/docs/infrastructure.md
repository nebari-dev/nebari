# Base Cost

The cluster has been preconfigured with cost in mind. We would like to
minimize cost when the cluster is not in use while providing the
ability to scale up.

{% if cookiecutter.provider == 'aws' %}

{% elif cookiecutter.provider == 'do' %}

DigitalOcean is the only provider that currently does not charge for
using kubernetes. The reason providers usually charge for Kubernetes
is that the cloud providers are managing the kubernetes master which
does have cost on their end. Thus the cost is simply the cost of the
Droplets. In the default configuration the minimum cost is $60.

 - general pool :: min 1  $20 <-> max 1 $20
 - user pool :: min 1 $20 <-> max 4 $80
 - worker pool :: min 1 $20 <-> max 6 $120

TODO: talk about cost of storage and load balancer (not yet
investigated).

{% elif cookiecutter.provider == 'gcp' %}

{% endif %}

# Autoscaling

{% if cookiecutter.provider == 'aws' %}

{% elif cookiecutter.provider == 'do' %}

DigitalOcean has a single limitation on autoscaling that the min size
must be at least 1. Nodes take around 1 minute to apear within the
node group.

{% elif cookiecutter.provider == 'gcp' %}

{% endif %}

