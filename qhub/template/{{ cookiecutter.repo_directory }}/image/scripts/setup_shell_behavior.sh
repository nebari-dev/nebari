#!/bin/bash

DEFAULT_ENV="$1"; shift

# Setup some basic terminal setting using the bash skeleton
cp /etc/skel/.bashrc /etc/profile.d/term_settings.sh
sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/profile.d/term_settings.sh

# Always try to activate default conda environment (in /etc/profile.d)
cat << \EOF > /etc/profile.d/PATH_modification.sh
PATH="$PATH:/opt/scripts"
PATH="$NVIDIA_PATH:$PATH"
EOF

# Define ETC_BASHRC_WAS_SOURCED in bash.bashrc which is sourced for interactive
# shells.
echo "ETC_BASHRC_WAS_SOURCED=yes" >> /etc/bash.bashrc
echo "source /etc/profile" >> /etc/bash.bashrc

# Create and /etc/profile that reciprocally sources bash.bashrc so that basic
# env is always the same regardless of whether  a login shell is used.
# Quotes in the following line make the heredoc defined below verbatim
# (variables are not substituted.
cat << "EOF" > /etc/profile
# /etc/profile: system-wide .profile file for the Bourne shell (sh(1))
# and Bourne compatible shells (bash(1), ksh(1), ash(1), ...).

# Initialize PATH. Subsequent modifications should be made in /etc/profile.d
if [ "`id -u`" -eq 0 ]; then
  PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
else
  PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games"
fi
export PATH

umask 002

if [ "${PS1-}" ]; then
  if [ "${BASH-}" ] && [ "$BASH" != "/bin/sh" ]; then
    # The file bash.bashrc already sets the default PS1.
    # PS1='\h:\w\$ '
    [[ ${ETC_BASHRC_WAS_SOURCED} != yes && -f /etc/bash.bashrc ]] && source /etc/bash.bashrc
  else
    if [ "`id -u`" -eq 0 ]; then
      PS1='# '
    else
      PS1='$ '
    fi
  fi
fi

##### Always run after /etc/bash.bashrc ####

# basic config for all users
if [ -d /etc/profile.d ]; then
  for i in /etc/profile.d/*.sh; do
    if [ -r $i ]; then
      . $i
    fi
  done
  unset i
fi

# custom config that can be set on a deployment specific basis
if [ -d /etc/profile.d/custom_config_scripts ]; then
  for i in /etc/profile.d/custom_config_scripts/*.sh; do
    if [ -r $i ]; then
      . $i
    fi
  done
  unset i
fi

# modify the PATH to activate the appropriate default conda environment last...
if [ -f /opt/conda/etc/profile.d/conda.sh ];then
  # conda has been successfully installed and the conda.sh
  # has been linked appropriately... if nothing has been
  # activated already we should do that...
  if ! which conda; then
    . /opt/conda/etc/profile.d/conda.sh
    conda activate "${DEFAULT_ENV}"
  fi
fi

EOF
