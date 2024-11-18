#!/bin/bash -e

%{ if length(ami_id) > 0 ~}
# Set variables for custom AMI
export API_SERVER_URL="${cluster_endpoint}"
export B64_CLUSTER_CA="${cluster_cert_authority}"
%{ for k, v in bootstrap_env ~}
export ${k}="${v}"
%{ endfor ~}
export KUBELET_EXTRA_ARGS="--node-labels=eks.amazonaws.com/nodegroup-image=${ami_id},dedicated=${node_group_name},eks.amazonaws.com/capacityType=ON_DEMAND,eks.amazonaws.com/nodegroup=${node_group_name} --max-pods=58 ${kubelet_extra_args}"

# Call bootstrap for EKS optimized custom AMI
/etc/eks/bootstrap.sh ${cluster_name} --apiserver-endpoint "${API_SERVER_URL}" --b64-cluster-ca "${B64_CLUSTER_CA}" --kubelet-extra-args "${KUBELET_EXTRA_ARGS}"
%{ endif ~}
