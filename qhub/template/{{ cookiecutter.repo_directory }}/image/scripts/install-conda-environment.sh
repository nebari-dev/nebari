#!/usr/bin/env bash
set -xe
ENV_FILE="${1}"; shift # path to environment yaml or lock file 
NEW_ENV="${1}"; shift # true or false indicating whether env update should occur

# Capture last optional arg or set a ENV_NAME. This can be changed but be
# careful... setting the path for both the dockerfile and runtime container
# can be tricky
if [[ -z "${1+x}" ]] || [[ "${1}" == "" ]]; then
    ENV_NAME=default
else
    ENV_NAME="${1}"; shift
fi

# Set a default value for skipping the conda solve (using a lock file).
: ${SKIP_CONDA_SOLVE:=no}

# ==== install conda dependencies ====

if ! ${NEW_ENV};then
    if [[ $(basename "${ENV_FILE}") =~ "*lock*" ]];then
        echo "${ENV_FILE} should not be a lock file as this is not  supported when \
            only updating the conda environment. Consider setting NEW_ENV to yes."
        exit 1
    fi
    echo Installing into current conda environment
    conda env update -f "${ENV_FILE}"

# Env not being updated... create one now:
elif [[ "${SKIP_CONDA_SOLVE}" == "no" ]];then
    conda env create --prefix=/opt/conda/envs/${ENV_NAME} -f "${ENV_FILE}"
elif [[ "${SKIP_CONDA_SOLVE}" == "yes" ]];then
    conda create --prefix=/opt/conda/envs/${ENV_NAME} --file "${ENV_FILE}"

    # This needs to be set using the ENV directive in the docker file
    PATH="/opt/conda/envs/${ENV_NAME}/bin:${PATH}"
    # For now install pip section manually. We could consider using pip-tools...
    # See https://github.com/conda-incubator/conda-lock/issues/4
    pip install https://github.com/dirkcgrunwald/jupyter_codeserver_proxy-/archive/5596bc9c2fbd566180545fa242c659663755a427.tar.gz
else
    echo "SKIP_CONDA_SOLVE should be yes or no instead got: '${SKIP_CONDA_SOLVE}'"
    exit 1
fi

# ========= list dependencies ========
/opt/conda/bin/conda list

# ========== cleanup conda ===========
/opt/conda/bin/conda clean -afy
# remove unnecissary files (statis, js.maps)
find /opt/conda/ -follow -type f -name '*.a' -delete
find /opt/conda/ -follow -type f -name '*.js.map' -delete

# Fix permissions 
fix-permissions "/opt/conda/envs/${ENV_NAME}" || fix-permissions /opt/conda/bin
