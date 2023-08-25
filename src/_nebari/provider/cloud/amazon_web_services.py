import functools
import os
import re
import time
from typing import List

import boto3
from botocore.exceptions import ClientError

from _nebari import constants
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version

MAX_RETRIES = 5
DELAY = 5


def check_credentials():
    for variable in {
        "AWS_DEFAULT_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    }:
        if variable not in os.environ:
            raise ValueError(
                f"""Missing the following required environment variable: {variable}\n
                Please see the documentation for more information: {constants.AWS_ENV_DOCS}"""
            )


def aws_session(digitalocean_region: str = None):
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
        region = os.environ["AWS_DEFAULT_REGION"]

    return boto3.Session(
        region_name=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )


@functools.lru_cache()
def regions():
    session = aws_session()
    ec2_client = session.client("ec2")
    regions = ec2_client.describe_regions()["Regions"]
    return {_["RegionName"]: _["RegionName"] for _ in regions}


@functools.lru_cache()
def zones():
    session = aws_session()
    client = session.client("ec2")

    response = client.describe_availability_zones()
    return {_["ZoneName"]: _["ZoneName"] for _ in response["AvailabilityZones"]}


@functools.lru_cache()
def kubernetes_versions():
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    # AWS SDK (boto3) currently doesn't offer an intuitive way to list available kubernetes version. This implementation grabs kubernetes versions for specific EKS addons. It will therefore always be (at the very least) a subset of all kubernetes versions still supported by AWS.
    session = aws_session()
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
def instances():
    session = aws_session()
    client = session.client("ec2")
    paginator = client.get_paginator("describe_instance_types")
    instance_types = sorted(
        [j["InstanceType"] for i in paginator.paginate() for j in i["InstanceTypes"]]
    )
    return {t: t for t in instance_types}


def aws_get_vpc_id(name: str, namespace: str) -> str:
    cluster_name = f"{name}-{namespace}"
    session = aws_session()
    client = session.client("ec2")
    response = client.describe_vpcs()

    for vpc in response["Vpcs"]:
        tags = vpc.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                return vpc["VpcId"]


def aws_get_subnet_ids(name: str, namespace: str) -> List[str]:
    session = aws_session()
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


def aws_get_route_table_ids(name: str, namespace: str) -> List[str]:
    cluster_name = f"{name}-{namespace}"
    session = aws_session()
    client = session.client("ec2")
    response = client.describe_route_tables()

    routing_table_ids = []
    for routing_table in response["RouteTables"]:
        tags = routing_table.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                routing_table_ids.append(routing_table["RouteTableId"])

    return routing_table_ids


def aws_get_internet_gateway_ids(name: str, namespace: str) -> List[str]:
    cluster_name = f"{name}-{namespace}"
    session = aws_session()
    client = session.client("ec2")
    response = client.describe_internet_gateways()

    internet_gateways = []
    for internet_gateway in response["InternetGateways"]:
        tags = internet_gateway.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                internet_gateways.append(internet_gateway["InternetGatewayId"])

    return internet_gateways


def aws_get_security_group_ids(name: str, namespace: str) -> List[str]:
    cluster_name = f"{name}-{namespace}"
    session = aws_session()
    client = session.client("ec2")
    response = client.describe_security_groups()

    security_group_ids = []
    for security_group in response["SecurityGroups"]:
        tags = security_group.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == cluster_name:
                security_group_ids.append(security_group["GroupId"])

    return security_group_ids


def aws_get_load_balancer_name(vpc_id: str) -> str:
    if not vpc_id:
        print("No VPC ID provided. Exiting...")
        return

    session = aws_session()
    client = session.client("elb")
    response = client.describe_load_balancers()["LoadBalancerDescriptions"]

    for load_balancer in response:
        if load_balancer["VPCId"] == vpc_id:
            return load_balancer["LoadBalancerName"]


def aws_get_efs_ids(name: str, namespace: str) -> List[str]:
    session = aws_session()
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


def aws_get_efs_mount_target_ids(efs_id: str) -> List[str]:
    if not efs_id:
        print("No EFS ID provided. Exiting...")
        return

    session = aws_session()
    client = session.client("efs")
    response = client.describe_mount_targets(FileSystemId=efs_id)

    mount_target_ids = []
    for mount_target in response["MountTargets"]:
        mount_target_ids.append(mount_target["MountTargetId"])

    return mount_target_ids


def aws_get_ec2_volume_ids(name: str, namespace: str) -> List[str]:
    cluster_name = f"{name}-{namespace}"
    session = aws_session()
    client = session.client("ec2")
    response = client.describe_volumes()

    volume_ids = []
    for volume in response["Volumes"]:
        tags = volume.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "KubernetesCluster" and tag["Value"] == cluster_name:
                volume_ids.append(volume["VolumeId"])

    return volume_ids


def aws_get_iam_policy(name: str = None, pattern: str = None) -> str:
    session = aws_session()
    client = session.client("iam")
    response = client.list_policies(Scope="Local")

    for policy in response["Policies"]:
        if (name and policy["PolicyName"] == name) or (
            pattern and re.match(pattern, policy["PolicyName"])
        ):
            return policy["Arn"]


def aws_delete_load_balancer(name: str, namespace: str):
    vpc_id = aws_get_vpc_id(name, namespace)
    if not vpc_id:
        print("No VPC ID provided. Exiting...")
        return

    load_balancer_name = aws_get_load_balancer_name(vpc_id)

    session = aws_session()
    client = session.client("elb")

    try:
        print("here")
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
            client.describe_load_balancers(LoadBalancerNames=load_balancer_name)
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


def aws_delete_efs_mount_targets(efs_id: str):
    if not efs_id:
        print("No EFS provided. Exiting...")
        return

    session = aws_session()
    client = session.client("efs")

    mount_target_ids = aws_get_efs_mount_target_ids(efs_id)
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
        mount_target_ids = aws_get_efs_mount_target_ids(efs_id)
        if len(mount_target_ids) == 0:
            print(f"All mount targets for EFS {efs_id} deleted successfully")
            return
        else:
            print(f"Waiting for mount targets for EFS {efs_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_efs_file_system(efs_id: str):
    if not efs_id:
        print("No EFS provided. Exiting...")
        return

    session = aws_session()
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


def aws_delete_efs(name: str, namespace: str):
    efs_ids = aws_get_efs_ids(name, namespace)
    for efs_id in efs_ids:
        aws_delete_efs_mount_targets(efs_id)
        aws_delete_efs_file_system(efs_id)


def aws_delete_subnets(name: str, namespace: str):
    session = aws_session()
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace)
    subnet_ids = aws_get_subnet_ids(name, namespace)
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
        subnet_ids = aws_get_subnet_ids(name, namespace)
        if len(subnet_ids) == 0:
            print(f"All subnets for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for subnets for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_route_tables(name: str, namespace: str):
    session = aws_session()
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace)
    route_table_ids = aws_get_route_table_ids(name, namespace)
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
        route_table_ids = aws_get_route_table_ids(name, namespace)
        if len(route_table_ids) == 0:
            print(f"All route tables for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for route tables for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_internet_gateways(name: str, namespace: str):
    session = aws_session()
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace)
    internet_gateway_ids = aws_get_internet_gateway_ids(name, namespace)
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
        internet_gateway_ids = aws_get_internet_gateway_ids(name, namespace)
        if len(internet_gateway_ids) == 0:
            print(f"All internet gateways for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for internet gateways for VPC {vpc_id} to be detached...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_security_groups(name: str, namespace: str):
    session = aws_session()
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace)
    security_group_ids = aws_get_security_group_ids(name, namespace)
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
        security_group_ids = aws_get_security_group_ids(name, namespace)
        if len(security_group_ids) == 0:
            print(f"All security groups for VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for security groups for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_vpc(name: str, namespace: str):
    session = aws_session()
    client = session.client("ec2")

    vpc_id = aws_get_vpc_id(name, namespace)
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
        vpc_id = aws_get_vpc_id(name, namespace)
        if vpc_id is None:
            print(f"VPC {vpc_id} deleted successfully")
            return
        else:
            print(f"Waiting for VPC {vpc_id} to be deleted...")
            sleep_time = DELAY * (2**retries)
            time.sleep(sleep_time)
        retries += 1


def aws_delete_dynamodb_table(name: str):
    session = aws_session()
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


def aws_delete_ec2_volumes(name: str, namespace: str):
    session = aws_session()
    client = session.client("ec2")

    volume_ids = aws_get_ec2_volume_ids(name, namespace)
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
        volume_ids = aws_get_ec2_volume_ids(name, namespace)
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
    endpoint: str = None,
    digitalocean_region: str = None,
):
    session = aws_session(digitalocean_region=digitalocean_region)
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
    endpoint: str = None,
    digitalocean_region: str = None,
):
    aws_delete_s3_objects(bucket_name, endpoint, digitalocean_region)

    session = aws_session(digitalocean_region=digitalocean_region)
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


def aws_delete_iam_role_policies(role_name: str):
    session = aws_session()
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


def aws_delete_iam_policy(name: str):
    session = aws_session()
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


def aws_delete_iam_role(role_name: str):
    session = aws_session()
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


def aws_delete_node_groups(name: str, namespace: str):
    cluster_name = f"{name}-{namespace}"
    session = aws_session()
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


def aws_delete_cluster(name: str, namespace: str):
    cluster_name = f"{name}-{namespace}"
    session = aws_session()
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


def aws_cleanup(name: str, namespace: str):
    aws_delete_node_groups(name, namespace)
    aws_delete_cluster(name, namespace)

    aws_delete_load_balancer(name, namespace)

    aws_delete_efs(name, namespace)

    aws_delete_subnets(name, namespace)
    aws_delete_route_tables(name, namespace)
    aws_delete_internet_gateways(name, namespace)
    aws_delete_security_groups(name, namespace)
    aws_delete_vpc(name, namespace)

    aws_delete_ec2_volumes(name, namespace)

    dynamodb_table_name = f"{name}-{namespace}-terraform-state-lock"
    aws_delete_dynamodb_table(dynamodb_table_name)

    s3_bucket_name = f"{name}-{namespace}-terraform-state"
    aws_delete_s3_bucket(s3_bucket_name)

    iam_role_name = f"{name}-{namespace}-eks-cluster-role"
    iam_role_node_group_name = f"{name}-{namespace}-eks-node-group-role"
    iam_policy_name_regex = "^eks-worker-autoscaling-{name}-{namespace}(\\d+)$".format(
        name=name, namespace=namespace
    )
    iam_policy = aws_get_iam_policy(pattern=iam_policy_name_regex)
    if iam_policy:
        aws_delete_iam_role_policies(iam_role_node_group_name)
        aws_delete_iam_policy(iam_policy)
    aws_delete_iam_role(iam_role_name)
    aws_delete_iam_role(iam_role_node_group_name)
