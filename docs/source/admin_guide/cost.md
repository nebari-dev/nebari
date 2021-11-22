# Cloud cost and capabilities

Qhub doesn't charge a fee for infrastructure but cloud providers themselves have pricing for all their services. A digital ocean cluster's minimum fixed cost is around \$60/month. While other cloud providers fixed cost is around \$200/month. Each cloud vendor has different pricing and capabilities of their kubernetes offerings which can significantly affect the pricing of QHub. Cost alone doesn't determine which cloud is best for your use case. Often times you can't choose the cloud that QHub runs on. In this case this document can help determine a reasonable cost for running QHub. Keep in mind these numbers are a simplified view of pricing and won't reflect your actual bill.

## Kubernetes

Often cloud providers have a fixed cost for using kubernetes. Here is a table of capabilities of each cloud kubernetes offering along with costs:

| Cloud                                                                         | Pricing   | Scale to 0? | Spot/Preemptible? | GPUs |
|:------------------------------------------------------------------------------|:----------|:------------|------------------|:-----|
| [Digital Ocean Kubernetes](https://www.digitalocean.com/products/kubernetes/) | 0         | No          | No               | No   |
| [Google Compute Platform GKE](https://cloud.google.com/kubernetes-engine/)    | $75/month | Yes         | Yes              | Yes  |
| [Amazon Web Services](https://aws.amazon.com/eks/)                            | $75/month | No          | Yes              | Yes  |
| [Azure AKS](https://azure.microsoft.com/en-us/services/kubernetes-service/)   | $75/month | Yes         | Yes              | Yes  |

## Network costs

All cloud providers charge for egress. Egress is the traffic leaving their cloud service. Additionally QHub sets up a single load balancer that all traffic goes through.

| Cloud                 | Egress        | Load Balancer |
|:----------------------|:--------------|:--------------|
| Digital Ocean         | $0.01/GB      | $10/month     |
| Google Cloud Platform | $0.12-0.08/GB | $200/month    |
| Amazon Web Services   | $0.09-0.05/GB | $20/month     |
| Azure                 | $0.08-0.05/GB | $20/month     |

## Storage costs

Cloud providers provide many different types of storage. The include S3 like [object storage](https://en.wikipedia.org/wiki/Object_storage), [block storage](https://en.wikipedia.org/wiki/Block_(data_storage)), and traditional [filesystem storage](https://en.wikipedia.org/wiki/File_system). Note that each type of storage has well known advantages and limitations.

- Object storage is optimized for cost, bandwidth, and the cost of latency for file access. It directly affects the number of IOPs S3 is capable of. Object storage always provides the highest bandwidth. It does provide parallel partial access to files.
- Block storage is equivalent to a physical disk attached to your machine. Block storage offers high [IOPs](https://en.wikipedia.org/wiki/IOPS) for latency sensitive filesystem operations. They offer high bandwidth similar to object storage but at around 2-4 times the cost.
- Filesystem storage enables shared filesystems between multiple compute notes but at significant cost. NFS filesystem have significantly lower IOPS than block storage and significantly lower bandwidth than object storage. Usually the users choose this option due to needing to share files between multiple machines. This offering should be a last choice due to costing around $0.20/GB.

| Cloud                 | Object   | Block         | Filesystem                       |
|:----------------------|:---------|:--------------|----------------------------------|
| Digital Ocean         | $0.02/GB | $0.10/GB      | N/A                              |
| Google Cloud Platform | $0.02/GB | $0.4-0.12/GB  | \$0.20-0.30/GB |
| Amazon Web Services   | $0.02/GB | $0.05-0.12/GB | $0.30/GB                         |
| Azure                 | $0.02/GB | $0.6-0.12/GB  | $0.16/GB                         |

Note that these prices can be deceptive to compare. Each cloud providers offering have wildly different guaranteed IOPs, burst IOPS, guaranteed bandwidth, and burst bandwidth.

## Compute costs

Cloud providers have huge offerings of compute instances. And this guide couldn't do it all justice. A standard 4 CPU/16 GB RAM is used to compare the cloud offerings. This should give a ballpark of the cost of running a compute instance. Note that all compute instances need an attached block storage usually at lest 10 GB. Comparing CPUs isn't a fair comparison due to computer architecture and clock rate.

| Cloud                 | 4 GB/16 RAM  | GPUs? | ARM? | Max CPUs | Max RAM |
|:----------------------|:-----------|:------|------|-----------------|---------|
| Digital Ocean         | $120/month | No    | No   | 40              | 256     |
| Google Cloud Platform | $100/month | Yes   | No   | 416             | 11776   |
| Amazon Web Services   | $100/month | Yes   | Yes  | 448             | 6144    |
| Azure                 | $120/month | Yes   | No   | 120             | 2400    |

The cloud prices are pretty much the same between cloud providers. For smaller instances, that aren't shown in the table, Digital Ocean can save some money.
