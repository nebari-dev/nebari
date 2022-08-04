import argparse
import logging
import pathlib
import time

from qhub.utils import check_cloud_credentials, load_yaml, timer

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Force Destroy AWS environment.")
    parser.add_argument("-c", "--config", help="qhub configuration", required=True)
    args = parser.parse_args()

    handle_force_destroy(args)


def handle_force_destroy(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    config = load_yaml(config_filename)

    # Don't verify(config) in case the schema has changed - just pick out the important bits and tear down

    force_destroy_configuration(config)


def parse_arn(arn):
    # http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    elements = arn.split(":", 5)
    result = {
        # "arn": elements[0],
        "partition": elements[1],
        "service": elements[2],
        "region": elements[3],
        "account": elements[4],
        "resource": elements[5],
        "resource_type": None,
        "arn": arn,  # Full ARN
    }
    if "/" in result["resource"]:
        result["resource_type"], result["resource"] = result["resource"].split("/", 1)
    elif ":" in result["resource"]:
        result["resource_type"], result["resource"] = result["resource"].split(":", 1)
    return result


def force_destroy_configuration(config):
    logging.info("""FORCE Removing all infrastructure (not using terraform).""")

    with timer(logging, "destroying QHub"):
        # 01 Check we have cloud details we need
        check_cloud_credentials(config)

        if config.get("provider", "") != "aws":
            raise ValueError("force-destroy currently only available for AWS")

        project_name = config.get("project_name", "").strip()

        if project_name == "":
            raise ValueError("project_name cannot be blank")

        if "amazon_web_services" not in config:
            raise ValueError(
                "amazon_web_services section must exist in qhub-config.yaml"
            )

        region = config["amazon_web_services"].get("region", "").strip()

        if region == "":
            raise ValueError(
                "amazon_web_services.region must exist in qhub-config.yaml"
            )

        logging.info(f"Remove AWS project {project_name} in region {region}")

        env = config.get("namespace", "dev").strip()

        # 02 Remove all infrastructure
        try:
            import boto3
        except ImportError:
            raise ValueError(
                "Please ensure boto3 package is installed using: pip install boto3==1.17.98"
            )

        restag = boto3.client("resourcegroupstaggingapi", region_name=region)

        filter_params = dict(
            TagFilters=[
                {
                    "Key": "Owner",
                    "Values": [
                        "terraform",
                        "terraform-state",
                    ],
                },
                {
                    "Key": "Environment",
                    "Values": [
                        env,
                    ],
                },
                {
                    "Key": "Project",
                    "Values": [
                        project_name,
                    ],
                },
            ],
            ResourcesPerPage=50,
        )

        resources = []

        response = restag.get_resources(**filter_params)

        resources.extend(response["ResourceTagMappingList"])

        while "PaginationToken" in response and response["PaginationToken"]:
            token = response["PaginationToken"]
            response = restag.get_resources(**filter_params, PaginationToken=token)
            resources.extend(response["ResourceTagMappingList"])

        # Load Balancer and other K8s-generated resources will need to be queried separately:

        filter_params = dict(
            TagFilters=[
                {
                    "Key": f"kubernetes.io/cluster/{project_name}-{env}",
                    "Values": [
                        "owned",
                    ],
                }
            ],
            ResourcesPerPage=50,
        )

        response = restag.get_resources(**filter_params)
        resources.extend(response["ResourceTagMappingList"])

        # IAM

        iam = boto3.resource("iam")
        for suffix in ("eks-cluster-role", "eks-node-group-role"):

            try:
                role = iam.Role(f"{project_name}-{env}-{suffix}")

                if role.tags is not None:

                    tags_dict = dict(
                        [(t["Key"], t.get("Value", "")) for t in role.tags]
                    )

                    if (
                        tags_dict.get("Owner", "") == "terraform"
                        and tags_dict.get("Environment", "") == env
                        and tags_dict.get("Project", "") == project_name
                    ):
                        resources.append({"ResourceARN": role.arn})

            except iam.meta.client.exceptions.NoSuchEntityException:
                pass

        # Summarize resources

        type_groups = {}
        for r in resources:
            de_arned = parse_arn(r["ResourceARN"])
            t = f"{de_arned['service']}-{de_arned['resource_type']}"
            type_groups.setdefault(t, []).append(de_arned)
            logging.info(r["ResourceARN"])

        logging.info([(k, len(v)) for k, v in type_groups.items()])

        # Order
        priority_types = (
            "eks-nodegroup",
            "eks-cluster",
            "elasticloadbalancing-loadbalancer",
            "ec2-internet-gateway",
            "ec2-route-table",
            "elasticfilesystem-file-system",
            "ec2-subnet",
            "ec2-security-group",
            "ec2-vpc",
            "ecr-repository",
            "dynamodb-table",
            "s3-None",
            "resource-groups-group",
            "iam-role",
        )

        for pt in priority_types:
            logging.info(f"Inspect {pt}")
            for r in type_groups.get(pt, []):
                if pt == "eks-nodegroup":
                    nodegroup_resource = r["resource"].split("/")

                    cluster_name = nodegroup_resource[0]
                    nodegroup_name = nodegroup_resource[1]

                    logging.info(f"Delete {nodegroup_name} on cluster {cluster_name}")

                    client = boto3.client("eks", region_name=region)
                    client.delete_nodegroup(
                        clusterName=cluster_name, nodegroupName=nodegroup_name
                    )

                elif pt == "eks-cluster":
                    logging.info(f"Delete EKS cluster {r['resource']}")

                    client = boto3.client("eks", region_name=region)

                    response = client.list_nodegroups(clusterName=r["resource"])
                    while len(response["nodegroups"]) > 0:
                        logging.info("Nodegroups still present, sleep 10")
                        time.sleep(10)
                        response = client.list_nodegroups(clusterName=r["resource"])

                    client.delete_cluster(name=r["resource"])

                elif pt == "elasticloadbalancing-loadbalancer":
                    client = boto3.client("elb", region_name=region)

                    logging.info(f"Inspect Load balancer {r['resource']}")

                    logging.info(f"Delete Load balancer {r['resource']}")
                    response = client.delete_load_balancer(
                        LoadBalancerName=r["resource"]
                    )

                elif pt == "ec2-route-table":
                    logging.info(f"Inspect route table {r['resource']}")
                    ec2 = boto3.resource("ec2", region_name=region)
                    route_table = ec2.RouteTable(r["resource"])

                    for assoc in route_table.associations:
                        logging.info(f"Delete route table assoc {assoc.id}")
                        assoc.delete()

                    time.sleep(10)

                    logging.info(f"Delete route table {r['resource']}")
                    route_table.delete()

                elif pt == "ec2-subnet":
                    logging.info(f"Inspect subnet {r['resource']}")
                    ec2 = boto3.resource("ec2", region_name=region)
                    subnet = ec2.Subnet(r["resource"])

                    for ni in subnet.network_interfaces.all():
                        ni.load()
                        # But can only detach if attached...
                        if ni.attachment:
                            ni.detach(DryRun=False, Force=True)
                            ni.delete()

                    logging.info(f"Delete subnet {r['resource']}")
                    subnet.delete(DryRun=False)

                elif pt == "ec2-security-group":
                    logging.info(f"Inspect security group {r['resource']}")
                    ec2 = boto3.resource("ec2", region_name=region)
                    security_group = ec2.SecurityGroup(r["resource"])

                    for ipperms in security_group.ip_permissions_egress:
                        security_group.revoke_egress(
                            DryRun=False, IpPermissions=[ipperms]
                        )

                    for ipperms in security_group.ip_permissions:
                        security_group.revoke_ingress(
                            DryRun=False, IpPermissions=[ipperms]
                        )

                    logging.info(f"Delete security group {r['resource']}")
                    security_group.delete(DryRun=False)

                elif pt == "ec2-internet-gateway":
                    logging.info(f"Inspect internet gateway {r['resource']}")

                    ec2 = boto3.resource("ec2", region_name=region)
                    internet_gateway = ec2.InternetGateway(r["resource"])

                    for attach in internet_gateway.attachments:
                        logging.info(f"Inspect IG attachment {attach['VpcId']}")
                        if attach.get("State", "") == "available":
                            logging.info(f"Detach from VPC {attach['VpcId']}")
                            internet_gateway.detach_from_vpc(VpcId=attach["VpcId"])

                    time.sleep(10)

                    logging.info(f"Delete internet gateway {r['resource']}")
                    internet_gateway.delete(DryRun=False)

                elif pt == "elasticfilesystem-file-system":
                    client = boto3.client("efs", region_name=region)

                    logging.info(f"Delete efs {r['resource']}")

                    mts = client.describe_mount_targets(FileSystemId=r["resource"])

                    for mt in mts["MountTargets"]:
                        client.delete_mount_target(MountTargetId=mt["MountTargetId"])

                    response = client.delete_file_system(FileSystemId=r["resource"])

                    ## Should wait until this returns botocore.errorfactory.FileSystemNotFound:
                    # response = client.describe_file_systems(
                    #    FileSystemId=r['resource']
                    # )

                elif pt == "ec2-vpc":
                    logging.info(f"Inspect VPC {r['resource']}")

                    ec2 = boto3.resource("ec2", region_name=region)

                    vpc = ec2.Vpc(r["resource"])

                    # for cidr_assoc in vpc.cidr_block_association_set:
                    #    logging.info(cidr_assoc)
                    #    r = vpc.disassociate_subnet_cidr_block(
                    #        AssociationId=cidr_assoc['AssociationId']
                    #    )
                    #    logging.info(r)

                    logging.info(f"Delete VPC {r['resource']}")
                    vpc.delete()

                elif pt == "ecr-repository":
                    logging.info(f"Inspect ECR {r['resource']}")
                    client = boto3.client("ecr", region_name=region)

                    logging.info(f"Delete ecr {r['account']} / {r['resource']}")

                    response = response = client.delete_repository(
                        registryId=r["account"],
                        repositoryName=r["resource"],
                        force=True,
                    )

                elif pt == "s3-None":
                    logging.info(f"Inspect S3 {r['resource']}")
                    s3 = boto3.resource("s3", region_name=region)

                    logging.info(f"Delete s3 {r['resource']}")

                    bucket = s3.Bucket(r["resource"])

                    r = bucket.objects.all().delete()

                    r = bucket.object_versions.delete()

                    response = bucket.delete()

                elif pt == "dynamodb-table":
                    logging.info(f"Inspect DynamoDB {r['resource']}")

                    client = boto3.client("dynamodb", region_name=region)

                    logging.info(f"Delete DynamoDB {r['resource']}")

                    response = client.delete_table(TableName=r["resource"])

                elif pt == "resource-groups-group":
                    logging.info(f"Inspect Resource Group {r['resource']}")

                    client = boto3.client("resource-groups", region_name=region)

                    logging.info(f"Delete Resource Group {r['resource']}")

                    response = client.delete_group(Group=r["arn"])

                elif pt == "iam-role":
                    logging.info(f"Inspect IAM Role {r['resource']}")
                    iam = boto3.resource("iam")
                    role = iam.Role(r["resource"])

                    for policy in role.attached_policies.all():
                        logging.info(f"Detach Role policy {policy.arn}")
                        response = role.detach_policy(PolicyArn=policy.arn)

                    logging.info(f"Delete IAM Role {r['resource']}")
                    role.delete()


if __name__ == "__main__":
    main()
