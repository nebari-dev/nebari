#!/bin/bash

DEFAULT_ENV="$1"; shift

# Setup some basic terminal setting using the bash skeleton
cp /etc/skel/.bashrc /etc/profile.d/term_settings.sh
sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/profile.d/term_settings.sh

# Always try to activate default conda environment.
cat << EOF > /etc/profile.d/conda_init.sh
. /opt/conda/etc/profile.d/conda.sh
conda activate "${DEFAULT_ENV}"
EOF

# Define ETC_BASHRC_WAS_SOURCED in bash.bashrc which is sourced for interactive
# shells. 
echo "ETC_BASHRC_WAS_SOURCED=yes" >> /etc/bash.bashrc
echo "source /etc/profile" >> /etc/bash.bashrc

# Create and /etc/profile that reciprocally sources bash.bashrc so that basic
# env is always the same.
# Quotes in the following line make the heredoc defined verbatim (variables are
# not substituted.
cat << "EOF" > /etc/profile
# /etc/profile: system-wide .profile file for the Bourne shell (sh(1))
# and Bourne compatible shells (bash(1), ksh(1), ash(1), ...).

if [ "`id -u`" -eq 0 ]; then
  PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
else
  PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games"
fi
export PATH

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

if [ -d /etc/profile.d ]; then
  for i in /etc/profile.d/*.sh; do
    if [ -r $i ]; then
      . $i
    fi
  done
  unset i
fi
EOF
