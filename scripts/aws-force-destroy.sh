#!/bin/bash

# Required CLIs: aws, kubectl

# parse optional flags
while getopts "yf:" opt
do
  case "$opt" in
    y) yes=true ;;
    f) file="$OPTARG" ;;
    *) echo "usage: $0 [-v] [-r]" >&2
       exit 1 ;;
  esac
done

PROJECT_NAME=${NEBARI_PROJECT_NAME:-}
NAMESPACE=${NEBARI_NAMESPACE:-}

if [ -z "$PROJECT_NAME" ]; then
    echo "Please set the NEBARI_PROJECT_NAME environment variable."
    exit 1
fi

if [ -z "$NAMESPACE" ]; then
    echo "Please set the NEBARI_NAMESPACE environment variable."
    exit 1
fi

echo "Set to force delete: $PROJECT_NAME-$NAMESPACE and associated resources. This may take as long as 30 mins."

# confirmation to delete
if ! [[ $yes ]]; then
    read -rep $'Do you wish to continue? [y/N] ' REPLY

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo $'Existing...\n'
        exit 1
    fi
fi

# default log file location
if ! [[ $file ]]; then
    file="./aws-force-destroy-logs.txt"
fi

echo "Writing all logs to: $file"


# send all output to log file
exec &> >(tee -a "$file")

echo $'Deleting the Nebari cluster on AWS now...'

echo "Deleting running pods on EKS cluster"
aws eks update-kubeconfig --name "${PROJECT_NAME}-${NAMESPACE}"
kubectl delete pods -n dev -l component=singleuser-server,app=jupyterhub

# delete and wait for worker nodegroup to be deleted
echo "Deleting EKS node-group: worker"
aws eks delete-nodegroup --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name worker
aws eks wait nodegroup-deleted --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name worker

# delete and wait for user nodegroup to be deleted
echo "Deleting EKS node-group: user"
aws eks delete-nodegroup --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name user
aws eks wait nodegroup-deleted --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name user

# delete and wait for general nodegroup to be deleted
echo "Deleting EKS node-group: general"
aws eks delete-nodegroup --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name general
aws eks wait nodegroup-deleted --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name general

# delete and wait for eks cluster to be deleted
echo "Deleting EKS cluster: $PROJECT_NAME-$NAMESPACE"
aws eks delete-cluster --name "${PROJECT_NAME}-${NAMESPACE}"
aws eks wait cluster-deleted --name "${PROJECT_NAME}-${NAMESPACE}"

# get VPC ID
vpcid=$(aws ec2 describe-vpcs --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query "Vpcs[0].VpcId" --output text)
echo "VPC ID: $vpcid"

if [ -z "$vpcid" ]; then
    echo "VPC with ID $vpcid does not exist."
else
    # get ELB name using VPC ID
    elbname=$(aws elb describe-load-balancers --query "LoadBalancerDescriptions[?starts_with(VPCId, '$vpcid')] | [0].LoadBalancerName" --output text)

    if [ -z "$elbname" ]; then
        echo "ELB with name $elbname does not exist."
    else
        # delete ELB
        echo "Deleting Elastic Load Balancer (ELB): ${elbname}"
        aws elb delete-load-balancer --load-balancer-name "$elbname"
    fi
fi


# get EFS ID
fsid=$(aws efs describe-file-systems --query "FileSystems[?starts_with(Name, '$PROJECT_NAME-$NAMESPACE')] | [0].FileSystemId" --output text)
echo "EFS ID: $fsid"

if [ -z "$fsid" ]; then
    echo "EFS with ID $fsid does not exist."
else
    # get EFS Mount Target ID (subnet a)
    fsmta=$(aws efs describe-mount-targets --file-system-id "$fsid" --query "MountTargets[0].MountTargetId" --output text)

    # get EFS Mount Target ID (subnet b)
    fsmtb=$(aws efs describe-mount-targets --file-system-id "$fsid" --query "MountTargets[1].MountTargetId" --output text)

    if [ -z "$fsmta" ]; then
        echo "EFS Mount with ID $fsmta does not exist."
    else
        # delete EFS Mount Target (subnet a)
        echo "Deleting Elastic File System (EFS) Mount Target 1: $fsmta"
        aws efs delete-mount-target --mount-target-id "$fsmta"
    fi

    if [ -z "$fsmtb" ]; then
        echo "EFS Mount with ID $fsmtb does not exist."
    else
        # delete EFS Mount Target (subnet b)
        echo "Deleting Elastic File System (EFS) Mount Target 2: $fsmtb"
        aws efs delete-mount-target --mount-target-id "$fsmtb"
    fi

    # to ensure all mount targets are deleted
    sleep 60

    # delete EFS
    echo "Deleting Elastic File System (EFS): $fsid"
    aws efs delete-file-system --file-system-id "$fsid"
fi

# TODO: add subnets to array and delete each individually
# get VPC Subnet IDs - possibly multiple
subneta=$(aws ec2 describe-subnets --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'Subnets[0].SubnetId' --output text)
subnetb=$(aws ec2 describe-subnets --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'Subnets[1].SubnetId' --output text)
echo "Subnet ID 1: $subneta"
echo "Subnet ID 2: $subnetb"

# delete VPC Subnets
if [ -z "$subneta" ]; then
    echo "No subnet with ID $subneta"
else
    echo "Deleting Virtual Private Network (VPC) Subnet 1: $subneta"
    aws ec2 delete-subnet --subnet-id "$subneta"
fi

if [ -z "$subnetb" ]; then
    echo "No subnet with ID $subnetb"
else
    echo "Deleting Virtual Private Network (VPC) Subnet 2: $subnetb"
    aws ec2 delete-subnet --subnet-id "$subnetb"
fi

# get VPC Route Table ID
rtid=$(aws ec2 describe-route-tables --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'RouteTables[0].RouteTableId' --output text)
echo "Route table ID: $rtid"

if [ -z "$rtid" ]; then
    echo "No route table with ID $rtid"
else
    # delete VPC Route Table
    echo "Deleting Virtual Private Network (VPC) Route Table"
    aws ec2 delete-route-table --route-table-id "$rtid"
fi

# get VPC Internet Gateway ID
igwid=$(aws ec2 describe-internet-gateways --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'InternetGateways[0].InternetGatewayId' --output text)
echo "Internet gateway ID: $igwid"

if [ -z "$igwid" ]; then
    echo "No internet gateway with ID $igwid"
else
    # detach Internet Gateway from VPC
    aws ec2 detach-internet-gateway --internet-gateway-id "$igwid" --vpc-id "$vpcid"

    # delete Internet Gateway from VPC
    echo "Deleting Virtual Private Network (VPC) Internet Gateway"
    aws ec2 delete-internet-gateway --internet-gateway-id "$igwid"
fi

# TODO: add security groups to array and delete each individually
# get VPC Security Group ID - possibly multiple
sgida=$(aws ec2 describe-security-groups --query "SecurityGroups[?starts_with(VpcId, '$vpcid')] | [0].GroupId" --output text)
sgidb=$(aws ec2 describe-security-groups --query "SecurityGroups[?starts_with(VpcId, '$vpcid')] | [1].GroupId" --output text)
echo "Security group ID 1: $sgida"
echo "Security group ID 2: $sgidb"

# delete VPC Security Group
if [ -z "$sgida" ]; then
    echo "No security group with ID: $sgida"
else
    echo "Deleting Virtual Private Network (VPC) Security Group: $sgida"
    aws ec2 delete-security-group --group-id "$sgida"
fi

if [ -z "$sgidb" ]; then
    echo "No security group with ID: $sgidb"
else
    echo "Deleting Virtual Private Network (VPC) Security Group: $sgidb"
    aws ec2 delete-security-group --group-id "$sgidb"
fi

if [ -z "$vpcid" ]; then
    echo "VPC with ID $vpcid does not exist."
else
    # delete VPC
    echo "Deleting Virtual Private Network (VPC): $vpcid"
    aws ec2 delete-vpc --vpc-id "$vpcid"
fi

# get S3 bucket name
s3name=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$PROJECT_NAME')] | [0].Name" --output text)
echo "S3 bucket name: $s3name"

if [ -z "$s3name" ]; then
    echo "S3 bucket with name $s3name does not exist."
else
    # delete S3 objects
    echo "Deleting S3 Objects"
    aws s3api delete-objects --bucket "$s3name" --delete "$(aws s3api list-object-versions --bucket "$s3name" --query '{Objects: Versions[].{Key: Key, VersionId: VersionId}}' --max-items 1000)"

    # delete S3 bucket
    echo "Deleting S3 Bucket: $s3name"
    aws s3api delete-bucket --bucket "$s3name"
fi

# delete DynamoDB table
echo "Deleting DynamoDB Table"
aws dynamodb delete-table --table-name "$PROJECT_NAME-$NAMESPACE-terraform-state-lock"

# delete Resource Group
echo "Deleting Resource Group"
aws resource-groups delete-group --group "$PROJECT_NAME"

volume_names=($(aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/${PROJECT_NAME}-${NAMESPACE},Values=owned" --query 'Volumes[?Tags[?Key==`Name`]].VolumeId'  --output text))

# delete EC2 volumes
for id in "${volume_names[@]}"; do
    echo "Deleting volume: $id"
    aws ec2 delete-volume --volume-id "$id"
done
