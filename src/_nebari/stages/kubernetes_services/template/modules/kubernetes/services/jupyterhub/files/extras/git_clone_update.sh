#!/bin/sh

################################################################################
# Git Clone and/or Update Script
#
# This script automates Git repository handling with the following features:
#
# 1. Clones/Updates a Git repository into a specified folder;
# 2. Creates a `.firstrun` file in the folder to mark the script's execution, ensuring it only runs once for each folder.
#
# Usage: ./git_clone_update.sh "<folder1> <git_repo_url1>" [...]
#   - <folderX>: Path to the folder where the Git repository will be cloned or updated.
#   - <git_repo_urlX>: URL of the Git repository to clone or update.
################################################################################

# Define colors for messages and command output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

ERROR_LOG=".git-sync-errors.txt"

echo -e "${GREEN}Starting execution...${NC}"

# Check if at least one pair of folder and git repo URL is provided
if [ "$#" -lt 1 ] || [ "$1" = "--help" ]; then
  echo "Usage: $0 \"<folder1> <git_repo_url1>\" \"<folder2> <git_repo_url2>\" ..."

  # Exit with status code 0 if '--help' is provided, otherwise exit with status code 1
  [ "$1" = "--help" ] && exit 0 || exit 1
fi

fix_parent_dir_permissions() {
  # Fix parent directory permissions to allow the JupyterLab user to access the cloned repository

  local folder_path="$1"

  # Retrieve the very first parent directory
  local parent_dir=$(echo "$folder_path" | cut -d '/' -f1)

  # Check if the parent directory has the correct permissions
  if [ "$(stat -c "%u:%g" "$parent_dir")" != "1000:100" ]; then
    echo "Fixing permissions for parent directory: $parent_dir"
    chown -R 1000:100 "$parent_dir" || { echo "Error: Unable to set ownership for $parent_dir"; return 1; }
    chmod -R 755 "$parent_dir" || { echo "Error: Unable to set permissions for $parent_dir"; return 1; }
  fi
}

clone_update_repository() {
  # Clone or update a Git repository into a specified folder,
  # and create a `.firstrun` file to mark the script's execution.

  local folder_path="$1"
  local git_repo_url="$2"

  local firstrun_file="$folder_path/.firstrun"

  if [ -f "$firstrun_file" ]; then
    echo -e "The script has already been run for ${folder_path}. Skipping. ${GREEN}✅${NC}"
  else
    if [ ! -d "$folder_path" ]; then
      mkdir -p "$folder_path"
    fi

    fix_parent_dir_permissions "$folder_path" || return 1

    if [ -d "$folder_path/.git" ]; then
      echo -e "Updating Git repository in ${folder_path}..."
      (cd "$folder_path" && git pull)
    else
      echo -e "Cloning Git repository to ${folder_path}..."
      (git clone "$git_repo_url" "$folder_path")
    fi

    echo -e "Creating .firstrun file in ${folder_path}..."
    touch "$firstrun_file"

    # User permissions for JupyterLab user to newly created git folders
    echo -e "Setting permissions for ${folder_path}..."
    chown -R 1000:100 "$folder_path" || { echo "Error: Unable to set ownership for $folder_path"; return 1; }

    echo -e "Execution for ${folder_path} completed. ${GREEN}✅${NC}"
  fi
}


# Iterate through pairs and run in parallel
for pair in "$@"; do
  # Split the pair into folder_path and git_repo_url using space as the delimiter
  folder_path=$(echo "$pair" | cut -d ' ' -f1)
  git_repo_url=$(echo "$pair" | cut -d ' ' -f2-)

  if [ -z "$folder_path" ] || [ -z "$git_repo_url" ]; then
    # Initialize error log
    echo -e "${RED}Invalid argument format: \"${pair}\". Please provide folder path and Git repository URL in the correct order.${NC}" >> "$ERROR_LOG"
  else
    clone_update_repository "$folder_path" "$git_repo_url" || echo -e "${RED}Error executing for ${folder_path}.${NC}" >> "$ERROR_LOG"
  fi
done

wait

if [ -s "$ERROR_LOG" ]; then
  echo -e "${RED}Some operations failed. See errors in '${ERROR_LOG}'.${NC}"
  chown 1000:100 "$ERROR_LOG"
else
  echo -e "${GREEN}All operations completed successfully. ✅${NC}"
fi
