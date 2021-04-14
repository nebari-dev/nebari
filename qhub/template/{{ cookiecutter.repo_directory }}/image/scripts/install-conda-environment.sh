#!/usr/bin/env bash
set -xe
ENV_FILE="${1}"; shift
# Capture last optional arg or set a ENV_NAME
if [[ -z "${1+x}" ]] || [[ "${1}" == "" ]]; then
    ENV_NAME=default
else
    ENV_NAME="${1}"; shift
fi

# ==== install conda dependencies ====
conda create --prefix=/opt/conda/envs/${ENV_NAME} --file "${ENV_FILE}"
PATH="/opt/conda/envs/${ENV_NAME}/bin:${PATH}"
# For now install pip section manually. We could consider using pip-tools...
# See https://github.com/conda-incubator/conda-lock/issues/4
pip install https://github.com/dirkcgrunwald/jupyter_codeserver_proxy-/archive/5596bc9c2fbd566180545fa242c659663755a427.tar.gz

# ========= list dependencies ========
/opt/conda/bin/conda list

# ========== cleanup conda ===========
/opt/conda/bin/conda clean -afy
# remove unnecissary files (statis, js.maps)
find /opt/conda/ -follow -type f -name '*.a' -delete
find /opt/conda/ -follow -type f -name '*.js.map' -delete
