#!/bin/bash

# Required CLIs: aws, kubectl

# optional bypass confirmation flag; -y == yes
while getopts y opt; do
    case $1 in
        -y|--yes) yes=true ;;
    esac
    shift
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

echo "Set to force delete: $PROJECT_NAME-$NAMESPACE. This may take as long as 30 mins."

# confirmation to delete
if ! [[ $yes ]]; then
    read -rep $'Do you wish to continue? [y/N] ' REPLY

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo $'Existing...\n'
        exit 1
    fi
fi


echo $'Deleting the Nebari cluster on AWS now...\n'

echo "Deleting running pods on EKS cluster"
aws eks update-kubeconfig --name "${PROJECT_NAME}-${NAMESPACE}"
kubectl delete pods -n dev -l component=singleuser-server,app=jupyterhub
echo "Running pods deleted."

# delete and wait for worker nodegroup to be deleted
echo -n "Deleting EKS node-group: worker"
aws eks delete-nodegroup --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name worker || true
aws eks wait nodegroup-deleted --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name worker || true
echo "EKS worker node-group deleted."

# delete and wait for user nodegroup to be deleted
echo -n "Deleting EKS node-group: user"
aws eks delete-nodegroup --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name user || true
aws eks wait nodegroup-deleted --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name user || true
echo "EKS user node-group deleted."

# delete and wait for general nodegroup to be deleted
echo -n "Deleting EKS node-group: general"
aws eks delete-nodegroup --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name general || true
aws eks wait nodegroup-deleted --cluster-name "${PROJECT_NAME}-${NAMESPACE}" --nodegroup-name general || true
echo "EKS general node-group deleted."

# delete and wait for eks cluster to be deleted
echo -n "Deleting EKS cluster: $PROJECT_NAME-$NAMESPACE"
aws eks delete-cluster --name "${PROJECT_NAME}-${NAMESPACE}" || true
aws eks wait cluster-deleted --name "${PROJECT_NAME}-${NAMESPACE}" || true
echo "EKS cluster deleted."

# get VPC ID
vpcid=$(aws ec2 describe-vpcs --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query "Vpcs[0].VpcId" --output text)

# get ELB name using VPC ID
elbname=$(aws elb describe-load-balancers --query "LoadBalancerDescriptions[?starts_with(VPCId, '$vpcid')] | [0].LoadBalancerName" --output text)

# delete ELB
echo -n "Deleting Elastic Load Balancer (ELB): ${elbname}"
aws elb delete-load-balancer --load-balancer-name $elbname
echo "ELB deleted."

# get EFS ID
fsid=$(aws efs describe-file-systems --query "FileSystems[?starts_with(Name, '$PROJECT_NAME-$NAMESPACE')] | [0].FileSystemId" --output text)

# get EFS Mount Target ID (subnet a)
fsmta=$(aws efs describe-mount-targets --file-system-id $fsid --query "MountTargets[0].MountTargetId" --output text)

# get EFS Mount Target ID (subnet b)
fsmtb=$(aws efs describe-mount-targets --file-system-id $fsid --query "MountTargets[1].MountTargetId" --output text)

# delete EFS Mount Target (subnet a)
echo -n "Deleting Elastic File System (EFS) Mount Target 1: $fsmta"
aws efs delete-mount-target --mount-target-id $fsmta
echo "EFS Mount Target 1 deleted."

# delete EFS Mount Target (subnet b)
echo -n "Deleting Elastic File System (EFS) Mount Target 2: $fsmtb"
aws efs delete-mount-target --mount-target-id $fsmtb
echo "EFS Mount Target 2 deleted."

# delete EFS
echo -n "Deleting Elastic File System (EFS): $fsid"
aws efs delete-file-system --file-system-id $fsid
echo "EFS deleted."

# get VPC Subnet ID (subnet b)
subneta=$(aws ec2 describe-subnets --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'Subnets[0].SubnetId' --output text)

# get VPC Subnet ID (subnet a)
subnetb=$(aws ec2 describe-subnets --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'Subnets[1].SubnetId' --output text)

# delete VPC Subnet (subnet a)
echo -n "Deleting Virtual Private Network (VPC) Subnet 1: $subneta"
aws ec2 delete-subnet --subnet-id $subneta
echo "VPC Subnet 1 deleted."

# delete VPC Subnet (subnet b)
echo -n "Deleting Virtual Private Network (VPC) Subnet 2: $subnetb"
aws ec2 delete-subnet --subnet-id $subnetb
echo "VPC Subnet 2 deleted."

# get VPC Route Table ID
rtid=$(aws ec2 describe-route-tables --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'RouteTables[0].RouteTableId' --output text)

# delete VPC Route Table
echo -n "Deleting Virtual Private Network (VPC) Route Table"
aws ec2 delete-route-table --route-table-id $rtid
echo "VPC Route Table deleted."

# get VPC Internet Gateway ID
igwid=$(aws ec2 describe-internet-gateways --filters "Name=tag:Project,Values='$PROJECT_NAME'" --query 'InternetGateways[0].InternetGatewayId' --output text)

# detach Internet Gateway from VPC
aws ec2 detach-internet-gateway --internet-gateway-id $igwid --vpc-id $vpcid

# delete Internet Gateway from VPC
echo -n "Deleting Virtual Private Network (VPC) Internet Gateway"
aws ec2 delete-internet-gateway --internet-gateway-id $igwid
echo "VPC Internet Gateway deleted."

# get VPC Security Group ID - possibly multiple
sgid=$(aws ec2 describe-security-groups --query "SecurityGroups[?starts_with(VpcId, '$vpcid')] | [0].GroupId" --output text)

# delete VPC Security Group
echo -n "Deleting Virtual Private Network (VPC) Security Group"
aws ec2 delete-security-group --group-id $sgid
echo "VPC Security Group deleted."

# delete VPC
echo -n "Deleting Virtual Private Network (VPC): $vpcid"
aws ec2 delete-vpc --vpc-id $vpcid
echo "VPC deleted."

# get S3 bucket name
s3name=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$PROJECT_NAME')] | [0].Name" --output text)

# delete S3 objects
echo -n "Deleting S3 Objects"
aws s3api delete-objects --bucket $s3name --delete "$(aws s3api list-object-versions --bucket $s3name --query '{Objects: Versions[].{Key: Key, VersionId: VersionId}}' --max-items 1000)"
echo "S3 Objects deleted."

# delete S3 bucket
echo -n "Deleting S3 Bucket: $s3name"
aws s3api delete-bucket --bucket $s3name
echo "S3 Bucket deleted."

# delete DynamoDB table
echo -n "Deleting DynamoDB Table"
aws dynamodb delete-table --table-name "$PROJECT_NAME-$NAMESPACE-terraform-state-lock"
echo "DynamoDB Table deleted."

# delete Resource Group
echo -n "Deleting Resource Group"
aws resource-groups delete-group --group $PROJECT_NAME
echo "Resource Group deleted."


# TODO: delete EC2 storage volumes
