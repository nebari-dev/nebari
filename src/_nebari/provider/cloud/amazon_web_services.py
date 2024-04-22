import functools
import os
import re
import time
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

from _nebari.constants import AWS_ENV_DOCS
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version
from _nebari.utils import check_environment_variables
from nebari import schema

MAX_RETRIES = 5
DELAY = 5


def check_credentials() -> None:
    required_variables = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}
    check_environment_variables(required_variables, AWS_ENV_DOCS)


@functools.lru_cache()
def aws_session(
    region: Optional[str] = None, digitalocean_region: Optional[str] = None
) -> boto3.Session:
    """Create a boto3 session."""
    if digitalocean_region:
        aws_access_key_id = os.environ["SPACES_ACCESS_KEY_ID"]
        aws_secret_access_key = os.environ["SPACES_SECRET_ACCESS_KEY"]
        region = digitalocean_region
        aws_session_token = None
    else:
        check_credentials()
        aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        aws_session_token = os.environ.get("AWS_SESSION_TOKEN")

        if not region:
            raise ValueError(
                "Please specify `region` in the nebari-config.yaml or if initializing the nebari-config, set the region via the "
                "`--region` flag or via the AWS_DEFAULT_REGION environment variable.\n"
            )

    return boto3.Session(
        region_name=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )


@functools.lru_cache()
def regions(region: str) -> Dict[str, str]:
    """Return dict of enabled regions for the AWS account.

    NOTE: This function attempts to call the EC2 describe_regions() API.
    If the API call fails, we catch the two most common exceptions:
      - EndpointConnectionError: This is raised when the region specified is invalid.
      - ClientError (AuthFailure): This is raised when the credentials are invalid or trying to specify a region in a non-standard partition (e.g. AWS GovCloud) or vice-versa.
    """
    session = aws_session(region=region)
    try:
        client = session.client("ec2")
        regions = client.describe_regions()["Regions"]
        return {_["RegionName"]: _["RegionName"] for _ in regions}
    except EndpointConnectionError as e:
        print("Please double-check that the region specified is valid.", e)
        exit(1)
    except ClientError as e:
        if "AuthFailure" in str(e):
            print(
                "Please double-check that the AWS credentials are valid and have the correct permissions.",
                "If you're deploying into a non-standard partition (e.g. AWS GovCloud), please ensure the region specified exists in that partition.",
            )
            exit(1)
        else:
            raise e


@functools.lru_cache()
def zones(region: str) -> Dict[str, str]:
    """Return dict of enabled availability zones for the AWS region."""
    session = aws_session(region=region)
    client = session.client("ec2")

    response = client.describe_availability_zones()
    return {_["ZoneName"]: _["ZoneName"] for _ in response["AvailabilityZones"]}


@functools.lru_cache()
def kubernetes_versions(region: str) -> List[str]:
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    # AWS SDK (boto3) currently doesn't offer an intuitive way to list available kubernetes version. This implementation grabs kubernetes versions for specific EKS addons. It will therefore always be (at the very least) a subset of all kubernetes versions still supported by AWS.
    session = aws_session(region=region)
    client = session.client("eks")

    supported_kubernetes_versions = list()
    available_addons = client.describe_addon_versions()
    for addon in available_addons.get("addons", None):
        for eksbuild in addon.get("addonVersions", None):
            for k8sversion in eksbuild.get("compatibilities", None):
                supported_kubernetes_versions.append(
                    k8sversion.get("clusterVersion", None)
                )

    supported_kubernetes_versions = sorted(list(set(supported_kubernetes_versions)))
    return filter_by_highest_supported_k8s_version(supported_kubernetes_versions)


@functools.lru_cache()
def instances(region: str) -> Dict[str, str]:
    """Return dict of available instance types for the AWS region."""
    session = aws_session(region=region)
    client = session.client("ec2")
    paginator = client.get_paginator("describe_instance_types")
    instance_types = sorted(
        [j["InstanceType"] for i in paginator.paginate() for j in i["InstanceTypes"]]
    )
    return {t: t for t in instance_types}


def aws_get_vpc_id(name: str, namespace: str, region: str) -> Optional[str]:
    """Return VPC ID for the EKS cluster namedd `{name}-{namespace}`."""
    cluster_name = f"{name}-{namespace}"
    session = aws_session(region=region)
    client = session.client("ec2")
    response = client.describe_vpcs()

    for vpc in response["Vpcs"]:
        tags = vpc.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                return vpc["VpcId"]
    return None


def set_asg_tags(asg_node_group_map: Dict[str, str], region: str) -> None:
    """Set tags for AWS node scaling from zero to work."""
    session = aws_session(region=region)
    autoscaling_client = session.client("autoscaling")
    tags = []
    for asg_name, node_group in asg_node_group_map.items():
        tags.append(
            {
                "Key": "k8s.io/cluster-autoscaler/node-template/label/dedicated",
                "Value": node_group,
                "ResourceId": asg_name,
                "ResourceType": "auto-scaling-group",
                "PropagateAtLaunch": True,
            }
        )
    autoscaling_client.create_or_update_tags(Tags=tags)


def aws_get_asg_node_group_mapping(
    name: str, namespace: str, region: str
) -> Dict[str, str]:
    """Return a dictionary of autoscaling groups and their associated node groups."""
    asg_node_group_mapping = {}
    session = aws_session(region=region)
    eks = session.client("eks")
    node_groups_response = eks.list_nodegroups(
        clusterName=f"{name}-{namespace}",
    )
    node_groups = node_groups_response.get("nodegroups", [])
    for nodegroup in node_groups:
        response = eks.describe_nodegroup(
            clusterName=f"{name}-{namespace}", nodegroupName=nodegroup
        )
        node_group_name = response["nodegroup"]["nodegroupName"]
        auto_scaling_groups = response["nodegroup"]["resources"]["autoScalingGroups"]
        for auto_scaling_group in auto_scaling_groups:
            asg_node_group_mapping[auto_scaling_group["name"]] = node_group_name
    return asg_node_group_mapping


def aws_get_subnet_ids(name: str, namespace: str, region: str) -> List[str]:
    """Return list of subnet IDs for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("ec2")
    response = client.describe_subnets()

    subnet_ids = []
    required_tags = 0
    for subnet in response["Subnets"]:
        tags = subnet.get("Tags", [])
        for tag in tags:
            if (
                tag["Key"] == "Project"
                and tag["Value"] == name
                or tag["Key"] == "Environment"
                and tag["Value"] == namespace
            ):
                required_tags += 1
        if required_tags == 2:
            subnet_ids.append(subnet["SubnetId"])
        required_tags = 0

    return subnet_ids


def aws_get_route_table_ids(name: str, namespace: str, region: str) -> List[str]:
    """Return list of route table IDs for the EKS cluster named `{name}-{namespace}`."""
    cluster_name = f"{name}-{namespace}"
    session = aws_session(region=region)
    client = session.client("ec2")
    response = client.describe_route_tables()

    routing_table_ids = []
    for routing_table in response["RouteTables"]:
        tags = routing_table.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                routing_table_ids.append(routing_table["RouteTableId"])

    return routing_table_ids


def aws_get_internet_gateway_ids(name: str, namespace: str, region: str) -> List[str]:
    """Return list of internet gateway IDs for the EKS cluster named `{name}-{namespace}`."""
    cluster_name = f"{name}-{namespace}"
    session = aws_session(region=region)
    client = session.client("ec2")
    response = client.describe_internet_gateways()

    internet_gateways = []
    for internet_gateway in response["InternetGateways"]:
        tags = internet_gateway.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                internet_gateways.append(internet_gateway["InternetGatewayId"])

    return internet_gateways


def aws_get_security_group_ids(name: str, namespace: str, region: str) -> List[str]:
    """Return list of security group IDs for the EKS cluster named `{name}-{namespace}`."""
    cluster_name = f"{name}-{namespace}"
    session = aws_session(region=region)
    client = session.client("ec2")
    response = client.describe_security_groups()

    security_group_ids = []
    for security_group in response["SecurityGroups"]:
        tags = security_group.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                security_group_ids.append(security_group["GroupId"])

    return security_group_ids


def aws_get_load_balancer_name(vpc_id: str, region: str) -> Optional[str]:
    """Return load balancer name for the VPC ID."""
    if not vpc_id:
        print("No VPC ID provided. Exiting...")
        return None

    session = aws_session(region=region)
    client = session.client("elb")
    response = client.describe_load_balancers()["LoadBalancerDescriptions"]

    for load_balancer in response:
        if load_balancer["VPCId"] == vpc_id:
            return load_balancer["LoadBalancerName"]
    return None


def aws_get_efs_ids(name: str, namespace: str, region: str) -> List[str]:
    """Return list of EFS IDs for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("efs")
    response = client.describe_file_systems()

    efs_ids = []
    required_tags = 0
    for efs in response["FileSystems"]:
        tags = efs.get("Tags", [])
        for tag in tags:
            if (
                tag["Key"] == "Project"
                and tag["Value"] == name
                or tag["Key"] == "Environment"
                and tag["Value"] == namespace
            ):
                required_tags += 1
        if required_tags == 2:
            efs_ids.append(efs["FileSystemId"])
        required_tags = 0

    return efs_ids


def aws_get_efs_mount_target_ids(efs_id: str, region: str) -> List[str]:
    """Return list of EFS mount target IDs for the EFS ID."""
    if not efs_id:
        print("No EFS ID provided. Exiting...")
        return []

    session = aws_session(region=region)
    client = session.client("efs")
    response = client.describe_mount_targets(FileSystemId=efs_id)

    mount_target_ids = []
    for mount_target in response["MountTargets"]:
        mount_target_ids.append(mount_target["MountTargetId"])

    return mount_target_ids


def aws_get_ec2_volume_ids(name: str, namespace: str, region: str) -> List[str]:
    """Return list of EC2 volume IDs for the EKS cluster named `{name}-{namespace}`."""
    cluster_name = f"{name}-{namespace}"
    session = aws_session(region=region)
    client = session.client("ec2")
    response = client.describe_volumes()

    volume_ids = []
    for volume in response["Volumes"]:
        tags = volume.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "KubernetesCluster" and tag["Value"] == cluster_name:
                volume_ids.append(volume["VolumeId"])

    return volume_ids


def aws_get_iam_policy(
    region: Optional[str], name: Optional[str] = None, pattern: Optional[str] = None
) -> Optional[str]:
    """Return IAM policy ARN for the policy name or pattern."""
    session = aws_session(region=region)
    client = session.client("iam")
    response = client.list_policies(Scope="Local")

    for policy in response["Policies"]:
        if (name and policy["PolicyName"] == name) or (
            pattern and re.match(pattern, policy["PolicyName"])
        ):
            return policy["Arn"]
    return None


def aws_delete_load_balancer(name: str, namespace: str, region: str):
    """Delete load balancer for the EKS cluster named `{name}-{namespace}`."""
    vpc_id = aws_get_vpc_id(name, namespace, region=region)
    if not vpc_id:
        print("No VPC ID provided. Exiting...")
        return

    load_balancer_name = aws_get_load_balancer_name(vpc_id, region=region)
    if not load_balancer_name:
        print("No load balancer found. Exiting...")
        return

    session = aws_session(region=region)
    client = session.client("elb")

    try:
        client.delete_load_balancer(LoadBalancerName=load_balancer_name)
        print(f"Initiated deletion for load balancer {load_balancer_name}")
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"Load balancer {load_balancer_name} not found. Exiting...")
            return
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            client.describe_load_balancers(LoadBalancerNames=[load_balancer_name])
            print(f"Waiting for load balancer {load_balancer_name} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        except ClientError as e:
            if "ResourceNotFoundException" in str(e):
                print(f"Load balancer {load_balancer_name} deleted successfully")
                return
            else:
                raise e
        retries += 1


def aws_delete_efs_mount_targets(efs_id: str, region: str):
    """Delete all mount targets for the EFS ID."""
    if not efs_id:
        print("No EFS provided. Exiting...")
        return

    session = aws_session(region=region)
    client = session.client("efs")

    mount_target_ids = aws_get_efs_mount_target_ids(efs_id, region=region)
    for mount_target_id in mount_target_ids:
        try:
            client.delete_mount_target(MountTargetId=mount_target_id)
            print(f"Initiated deletion for mount target {mount_target_id}")
        except ClientError as e:
            if "MountTargetNotFound" in str(e):
                print(f"Mount target {mount_target_id} not found. Exiting...")
            else:
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        mount_target_ids = aws_get_efs_mount_target_ids(efs_id, region=region)
        if len(mount_target_ids) == 0:
            print(f"All mount targets for EFS {efs_id} deleted successfully")
            return
        else:
            print(f"Waiting for mount targets for EFS {efs_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_efs_file_system(efs_id: str, region: str):
    """Delete EFS file system for the EFS ID."""
    if not efs_id:
        print("No EFS provided. Exiting...")
        return

    session = aws_session(region=region)
    client = session.client("efs")

    try:
        client.delete_file_system(FileSystemId=efs_id)
        print(f"Initiated deletion for EFS {efs_id}")
    except ClientError as e:
        if "FileSystemNotFound" in str(e):
            print(f"EFS {efs_id} not found. Exiting...")
            return
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            client.describe_file_systems(FileSystemId=efs_id)
            print(f"Waiting for EFS {efs_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        except ClientError as e:
            if "FileSystemNotFound" in str(e):
                print(f"EFS {efs_id} deleted successfully")
                return
            else:
                raise e
        retries += 1


def aws_delete_efs(name: str, namespace: str, region: str):
    """Delete EFS resources for the EKS cluster named `{name}-{namespace}`."""
    efs_ids = aws_get_efs_ids(name, namespace, region=region)
    for efs_id in efs_ids:
        aws_delete_efs_mount_targets(efs_id, region=region)
        aws_delete_efs_file_system(efs_id, region=region)


def aws_delete_subnets(name: str, namespace: str, region: str):
    """Delete all subnets for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace, region=region)
    subnet_ids = aws_get_subnet_ids(name, namespace, region=region)
    for subnet_id in subnet_ids:
        try:
            client.delete_subnet(SubnetId=subnet_id)
            print(f"Initiated deletion for subnet {subnet_id}")
        except ClientError as e:
            if "InvalidSubnetID.NotFound" in str(e):
                print(f"Subnet {subnet_id} not found. Exiting...")
            else:
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        subnet_ids = aws_get_subnet_ids(name, namespace, region=region)
        if len(subnet_ids) == 0:
            print(f"All subnets for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for subnets for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_route_tables(name: str, namespace: str, region: str):
    """Delete all route tables for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace, region=region)
    route_table_ids = aws_get_route_table_ids(name, namespace, region=region)
    for route_table_id in route_table_ids:
        try:
            client.delete_route_table(RouteTableId=route_table_id)
            print(f"Initiated deletion for route table {route_table_id}")
        except ClientError as e:
            if "InvalidRouteTableID.NotFound" in str(e):
                print(f"Route table {route_table_id} not found. Exiting...")
            else:
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        route_table_ids = aws_get_route_table_ids(name, namespace, region=region)
        if len(route_table_ids) == 0:
            print(f"All route tables for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for route tables for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_internet_gateways(name: str, namespace: str, region: str):
    """Delete all internet gateways for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace, region=region)
    internet_gateway_ids = aws_get_internet_gateway_ids(name, namespace, region=region)
    for internet_gateway_id in internet_gateway_ids:
        try:
            client.detach_internet_gateway(
                InternetGatewayId=internet_gateway_id, VpcId=vpc_id
            )
            client.delete_internet_gateway(InternetGatewayId=internet_gateway_id)
            print(
                f"Initiated deletion for internet gateway {internet_gateway_id} from VPC {vpc_id}"
            )
        except ClientError as e:
            if "InvalidInternetGatewayID.NotFound" in str(e):
                print(f"Internet gateway {internet_gateway_id} not found. Exiting...")
            else:
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        internet_gateway_ids = aws_get_internet_gateway_ids(
            name, namespace, region=region
        )
        if len(internet_gateway_ids) == 0:
            print(f"All internet gateways for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for internet gateways for VPC {vpc_id} to be detached...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_security_groups(name: str, namespace: str, region: str):
    """Delete all security groups for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace, region=region)
    security_group_ids = aws_get_security_group_ids(name, namespace, region=region)
    for security_group_id in security_group_ids:
        try:
            client.delete_security_group(GroupId=security_group_id)
            print(f"Initiated deletion for security group {security_group_id}")
        except ClientError as e:
            if "InvalidGroupID.NotFound" in str(e):
                print(f"Security group {security_group_id} not found. Exiting...")
            else:
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        security_group_ids = aws_get_security_group_ids(name, namespace, region=region)
        if len(security_group_ids) == 0:
            print(f"All security groups for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for security groups for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_vpc(name: str, namespace: str, region: str):
    """Delete VPC for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace, region=region)
    if vpc_id is None:
        print(f"No VPC {vpc_id} provided. Exiting...")
        return

    try:
        client.delete_vpc(VpcId=vpc_id)
        print(f"Initiated deletion for VPC {vpc_id}")
    except ClientError as e:
        if "InvalidVpcID.NotFound" in str(e):
            print(f"VPC {vpc_id} not found. Exiting...")
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        vpc_id = aws_get_vpc_id(name, namespace, region=region)
        if vpc_id is None:
            print(f"VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_dynamodb_table(name: str, region: str):
    """Delete DynamoDB table."""
    session = aws_session(region=region)
    client = session.client("dynamodb")

    try:
        client.delete_table(TableName=name)
        print(f"Initiated deletion for DynamoDB table {name}")
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"DynamoDB table {name} not found. Exiting...")
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            client.describe_table(TableName=name)
            print(f"Waiting for DynamoDB table {name} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        except ClientError as e:
            if "ResourceNotFoundException" in str(e):
                print(f"DynamoDB table {name} deleted successfully")
                return
            else:
                raise e
        retries += 1


def aws_delete_ec2_volumes(name: str, namespace: str, region: str):
    """Delete all EC2 volumes for the EKS cluster named `{name}-{namespace}`."""
    session = aws_session(region=region)
    client = session.client("ec2")

    volume_ids = aws_get_ec2_volume_ids(name, namespace, region=region)
    for volume_id in volume_ids:
        try:
            client.delete_volume(VolumeId=volume_id)
            print(f"Initiated deletion for volume {volume_id}")
        except ClientError as e:
            if "InvalidVolume.NotFound" in str(e):
                print(f"Volume {volume_id} not found. Exiting...")
            else:
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        volume_ids = aws_get_ec2_volume_ids(name, namespace, region=region)
        if len(volume_ids) == 0:
            print("All volumes deleted successfully")
            return
        else:
            print("Waiting for volumes to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_s3_objects(
    bucket_name: str,
    endpoint: Optional[str] = None,
    region: Optional[str] = None,
    digitalocean_region: Optional[str] = None,
):
    """
    Delete all objects in the S3 bucket.

    NOTE: This method is shared with Digital Ocean as their "Spaces" is S3 compatible and uses the same API.

    Parameters:
        bucket_name (str): S3 bucket name
        endpoint (str): S3 endpoint URL (required for Digital Ocean spaces)
        region (str): AWS region
        digitalocean_region (str): Digital Ocean region

    """
    session = aws_session(region=region, digitalocean_region=digitalocean_region)
    s3 = session.client("s3", endpoint_url=endpoint)

    try:
        s3_objects = s3.list_objects(Bucket=bucket_name)
        s3_objects = s3_objects.get("Contents")
        if s3_objects:
            for obj in s3_objects:
                s3.delete_object(Bucket=bucket_name, Key=obj["Key"])

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            print(f"Bucket {bucket_name} not found. Exiting...")
        else:
            raise e

    try:
        versioned_objects = s3.list_object_versions(Bucket=bucket_name)
        for version in versioned_objects.get("DeleteMarkers", []):
            print(version)
            s3.delete_object(
                Bucket=bucket_name, Key=version["Key"], VersionId=version["VersionId"]
            )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            print(f"Bucket {bucket_name} not found. Exiting...")
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            objs = s3.list_objects(Bucket=bucket_name)["ResponseMetadata"].get(
                "Contents"
            )
            if objs is None:
                print("Bucket objects all deleted successfully")
                return
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                print(f"Bucket {bucket_name} deleted successfully")
                return
            else:
                raise e
        retries += 1


def aws_delete_s3_bucket(
    bucket_name: str,
    endpoint: Optional[str] = None,
    region: Optional[str] = None,
    digitalocean_region: Optional[str] = None,
):
    """
    Delete S3 bucket.

    NOTE: This method is shared with Digital Ocean as their "Spaces" is S3 compatible and uses the same API.

    Parameters:
        bucket_name (str): S3 bucket name
        endpoint (str): S3 endpoint URL (required for Digital Ocean spaces)
        region (str): AWS region
        digitalocean_region (str): Digital Ocean region
    """
    aws_delete_s3_objects(bucket_name, endpoint, region, digitalocean_region)

    session = aws_session(region=region, digitalocean_region=digitalocean_region)
    s3 = session.client("s3", endpoint_url=endpoint)

    try:
        s3.delete_bucket(Bucket=bucket_name)
        print(f"Initiated deletion for bucket {bucket_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            print(f"Bucket {bucket_name} not found. Exiting...")
            return
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"Waiting for bucket {bucket_name} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        except ClientError as e:
            if (e.response["Error"]["Code"] == "NoSuchBucket") or (
                e.response["Error"]["Code"] == "NotFound"
            ):
                print(f"Bucket {bucket_name} deleted successfully")
                return
            else:
                raise e
        retries += 1


def aws_delete_iam_role_policies(role_name: str, region: str):
    """Delete all policies attached to the IAM role."""
    session = aws_session(region=region)
    iam = session.client("iam")

    try:
        response = iam.list_attached_role_policies(RoleName=role_name)
        for policy in response["AttachedPolicies"]:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy["PolicyName"])
            print(f"Delete IAM policy {policy['PolicyName']} from IAM role {role_name}")
    except ClientError as e:
        if "NoSuchEntity" in str(e):
            print(f"IAM role {role_name} not found. Exiting...")
        else:
            raise e


def aws_delete_iam_policy(name: str, region: str):
    """Delete IAM policy."""
    session = aws_session(region=region)
    iam = session.client("iam")

    try:
        iam.delete_policy(PolicyArn=name)
        print(f"Initiated deletion for IAM policy {name}")
    except ClientError as e:
        if "NoSuchEntity" in str(e):
            print(f"IAM policy {name} not found. Exiting...")
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            iam.get_policy(PolicyArn=name)
            print(f"Waiting for IAM policy {name} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        except ClientError as e:
            if "NoSuchEntity" in str(e):
                print(f"IAM policy {name} deleted successfully")
                return
            else:
                raise e
        retries += 1


def aws_delete_iam_role(role_name: str, region: str):
    """Delete IAM role."""
    session = aws_session(region=region)
    iam = session.client("iam")

    try:
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print(f"IAM role {role_name} not found. Exiting...")
            return
        else:
            raise e
    for policy in attached_policies["AttachedPolicies"]:
        iam.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])
        print(f"Detached policy {policy['PolicyName']} from role {role_name}")

        if policy["PolicyArn"].startswith("arn:aws:iam::aws:policy"):
            continue

        policy_versions = iam.list_policy_versions(PolicyArn=policy["PolicyArn"])

        for version in policy_versions["Versions"]:
            if not version["IsDefaultVersion"]:
                iam.delete_policy_version(
                    PolicyArn=policy["PolicyArn"], VersionId=version["VersionId"]
                )
                print(
                    f"Deleted version {version['VersionId']} of policy {policy['PolicyName']}"
                )

        iam.delete_policy(PolicyArn=policy["PolicyArn"])
        print(f"Deleted policy {policy['PolicyName']}")

    iam.delete_role(RoleName=role_name)
    print(f"Deleted role {role_name}")


def aws_delete_node_groups(name: str, namespace: str, region: str):
    """Delete all node groups for the EKS cluster named `{name}-{namespace}`."""
    cluster_name = f"{name}-{namespace}"
    session = aws_session(region=region)
    eks = session.client("eks")
    try:
        response = eks.list_nodegroups(clusterName=cluster_name)
        node_groups = response.get("nodegroups", [])
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"Cluster {cluster_name} not found. Exiting...")
            return
        else:
            raise e

    for node_group in node_groups:
        try:
            eks.delete_nodegroup(clusterName=cluster_name, nodegroupName=node_group)
            print(
                f"Initiated deletion for node group {node_group} belonging to cluster {cluster_name}"
            )
        except ClientError as e:
            if "ResourceNotFoundException" not in str(e):
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        pending_deletion = []

        for node_group in node_groups:
            try:
                response = eks.describe_nodegroup(
                    clusterName=cluster_name, nodegroupName=node_group
                )
                if response["nodegroup"]["status"] == "DELETING":
                    pending_deletion.append(node_group)
            except ClientError as e:
                if "ResourceNotFoundException" in str(e):
                    pass
                else:
                    raise e

        if not pending_deletion:
            print("All node groups have been deleted successfully.")
            return

        if retries < MAX_RETRIES - 1:
            sleep_time = DELAY * (2**retries)
            print(
                f"{len(pending_deletion)} node groups still pending deletion. Retrying in {sleep_time} seconds..."
            )
            time.sleep(sleep_time)

        retries += 1
        pending_deletion.clear()

    print(f"Failed to confirm deletion of all node groups after {MAX_RETRIES} retries.")


def aws_delete_cluster(name: str, namespace: str, region: str):
    """Delete EKS cluster named `{name}-{namespace}`."""
    cluster_name = f"{name}-{namespace}"
    session = aws_session(region=region)
    eks = session.client("eks")

    try:
        eks.delete_cluster(name=cluster_name)
        print(f"Initiated deletion for cluster {cluster_name}")
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"Cluster {cluster_name} not found. Exiting...")
            return
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = eks.describe_cluster(name=cluster_name)
            if response["cluster"]["status"] == "DELETING":
                sleep_time = DELAY * (2**retries)
                print(
                    f"Cluster {cluster_name} still pending deletion. Retrying in {sleep_time} seconds..."
                )
                time.sleep(sleep_time)
            else:
                raise ClientError(
                    f"Unexpected status for cluster {cluster_name}: {response['cluster']['status']}"
                )
        except ClientError as e:
            if "ResourceNotFoundException" in str(e):
                print(f"Cluster {cluster_name} has been deleted successfully.")
                return
            else:
                raise e

        retries += 1

    print(
        f"Failed to confirm deletion of cluster {cluster_name} after {MAX_RETRIES} retries."
    )


def aws_cleanup(config: schema.Main):
    """Delete all Amazon Web Services resources created by Nebari"""

    name = config.project_name
    namespace = config.namespace
    region = config.amazon_web_services.region

    aws_delete_node_groups(name, namespace, region)
    aws_delete_cluster(name, namespace, region)

    aws_delete_load_balancer(name, namespace, region)

    aws_delete_efs(name, namespace, region)

    aws_delete_subnets(name, namespace, region)
    aws_delete_route_tables(name, namespace, region)
    aws_delete_internet_gateways(name, namespace, region)
    aws_delete_security_groups(name, namespace, region)
    aws_delete_vpc(name, namespace, region)

    aws_delete_ec2_volumes(name, namespace, region)

    dynamodb_table_name = f"{name}-{namespace}-terraform-state-lock"
    aws_delete_dynamodb_table(dynamodb_table_name, region)

    s3_bucket_name = f"{name}-{namespace}-terraform-state"
    aws_delete_s3_bucket(s3_bucket_name, region)

    iam_role_name = f"{name}-{namespace}-eks-cluster-role"
    iam_role_node_group_name = f"{name}-{namespace}-eks-node-group-role"
    iam_policy_name_regex = "^eks-worker-autoscaling-{name}-{namespace}(\\d+)$".format(
        name=name, namespace=namespace
    )
    iam_policy = aws_get_iam_policy(region, pattern=iam_policy_name_regex)
    if iam_policy:
        aws_delete_iam_role_policies(iam_role_node_group_name, region)
        aws_delete_iam_policy(iam_policy, region)
    aws_delete_iam_role(iam_role_name, region)
    aws_delete_iam_role(iam_role_node_group_name, region)


### PYDANTIC VALIDATORS ###


def validate_region(region: str) -> str:
    """Validate that the region is one of the enabled AWS regions"""
    available_regions = regions(region=region)
    if region not in available_regions:
        raise ValueError(
            f"Region {region} is not one of available regions {available_regions}"
        )
    return region


def validate_kubernetes_versions(region: str, kubernetes_version: str) -> str:
    """Validate that the Kubernetes version is available in the specified region"""
    available_versions = kubernetes_versions(region=region)
    if kubernetes_version not in available_versions:
        raise ValueError(
            f"Kubernetes version {kubernetes_version} is not one of available versions {available_versions}"
        )
    return kubernetes_version
