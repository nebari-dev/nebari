#!/bin/bash

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
NC='\033[0m' # No Color

# Error log file
ERROR_LOG=".git-sync-errors.txt"

# Initialize error log
echo -n "" > "$ERROR_LOG"

echo -e "${GREEN}Starting execution...${NC}"

# Check if at least one pair of folder and git repo URL is provided
if [ "$#" -lt 1 ] || [ "$1" = "--help" ]; then
  echo "Usage: $0 \"<folder1> <git_repo_url1>\" \"<folder2> <git_repo_url2>\" ..."

  # Exit with status code 0 if '--help' is provided, otherwise exit with status code 1
  [ "$1" = "--help" ] && exit 0 || exit 1
fi

clone_update_repository() {
  # Clone or update a Git repository into a specified folder,
  # and create a `.firstrun` file to mark the script's execution.

  local folder_path="$1"
  local git_repo_url="$2"

  local firstrun_file="$folder_path/.firstrun"

  # Check if the .firstrun file exists
  if [ -f "$firstrun_file" ]; then
    echo -e "The script has already been run for ${folder_path}. Skipping. ${GREEN}✅${NC}"
  else
    if [ ! -d "$folder_path" ]; then
      mkdir -p "$folder_path"
    fi

    # Perform Git clone or update
    if [ -d "$folder_path/.git" ]; then
      echo -e "Updating Git repository in ${folder_path}..."
      (cd "$folder_path" && git pull)  # Wrap git pull command output in parentheses
    else
      echo -e "Cloning Git repository to ${folder_path}..."
      (git clone "$git_repo_url" "$folder_path")  # Wrap git clone command output in parentheses
    fi

    touch "$firstrun_file"
    echo -e "Execution for ${folder_path} completed. ${GREEN}✅${NC}"
  fi
}

# Iterate through pairs and run in parallel
for pair in "$@"; do
  read -r folder_path git_repo_url <<< "$pair"

  if [ -z "$folder_path" ] || [ -z "$git_repo_url" ]; then
    echo -e "${RED}Invalid argument format: \"${pair}\". Please provide folder path and Git repository URL in the correct order.${NC}"
  else
    clone_update_repository "$folder_path" "$git_repo_url" || echo -e "${RED}Error executing for ${folder_path}.${NC}" >> "$ERROR_LOG"
  fi
done

# Wait for all background processes to complete
wait

# Check if there were errors
if [ -s "$ERROR_LOG" ]; then
  echo -e "${RED}Some operations failed. See errors in '${ERROR_LOG}'.${NC}"
else
  echo -e "${GREEN}All operations completed successfully. ✅${NC}"
fi
