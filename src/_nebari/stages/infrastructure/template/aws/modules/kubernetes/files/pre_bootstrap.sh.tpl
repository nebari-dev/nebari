#!/bin/bash -e

%{ if length(bootstrap_env) > 0 ~}
# Set bootstrap environment variables
cat <<EOF > /etc/profile.d/eks-bootstrap-env.sh
#!/bin/bash
%{ for k, v in bootstrap_env ~}
export ${k}="${v}"
%{ endfor ~}
export ADDITIONAL_KUBELET_EXTRA_ARGS="${kubelet_extra_args}"
EOF

# Source the environment variables in the bootstrap script
echo -e "\nsource /etc/profile.d/eks-bootstrap-env.sh" >> /etc/eks/bootstrap.sh

# Merge ADDITIONAL_KUBELET_EXTRA_ARGS into KUBELET_EXTRA_ARGS
sed -i 's/^KUBELET_EXTRA_ARGS="${KUBELET_EXTRA_ARGS:-}/KUBELET_EXTRA_ARGS="${KUBELET_EXTRA_ARGS:-} ${ADDITIONAL_KUBELET_EXTRA_ARGS}/' /etc/eks/bootstrap.sh
%{ endif ~}

# User supplied pre-bootstrap commands
${pre_bootstrap_script}
