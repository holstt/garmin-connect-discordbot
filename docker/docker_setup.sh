#!/bin/bash
set -e
echo "Running script: $0"

# This script
# - Creates a dedicated system user for the container
# - Ensures a data directory for the container exists on host with most restrictive permissions
# - Ensures the .env file has most restrictive permissions
# NB! If running in WSL:
# - By defualt, Linux permissions are not supported, so commands changing permissions will have no effect

# Check if the script is run as root or with sudo privileges
if [ "$(id -u)" -ne 0 ]; then
  echo "Error: This script must be run as root or with sudo privileges."
  exit 1
fi

# Get args
USERNAME=$1
CONTAINER_DATA_DIR=$2
ENV_PATH=$3
COMMAND=$4

# Ensure arguments are provided
if [ -z "$USERNAME" ] || [ -z "$CONTAINER_DATA_DIR" ] || [ -z "$ENV_PATH" ] || [ -z "$COMMAND" ]; then
  echo "Error: Missing arguments. Usage: ./docker_setup.sh <username> <container_data_dir> <env_path> <command>"
  exit 1
fi

echo "Docker setup started"

# Create system user (or ensure created)
sudo adduser --system --disabled-login --disabled-password --no-create-home "$USERNAME"

# Create a dedicated group for the container and add the user to it
sudo groupadd "$USERNAME" && echo "Group $USERNAME created"
sudo usermod -aG "$USERNAME" "$USERNAME"

# Set up data directory for the container to store its data on host
sudo mkdir -p "$CONTAINER_DATA_DIR" && echo "Ensure created directory: $CONTAINER_DATA_DIR"
sudo chown "$USERNAME":"$USERNAME" "$CONTAINER_DATA_DIR"
# Restrict access to the data directory (all permissions to user only), such that we can store sensitive data
sudo chmod 700 "$CONTAINER_DATA_DIR"

# Ensure permission for env path
sudo chown "$USERNAME":"$USERNAME" "$ENV_PATH"
# Restrict access, readable by user only
sudo chmod 400 "$ENV_PATH"

echo "Docker setup complete."

# Run the project
echo "Running docker-compose project"
cd "$SCRIPT_DIR"

# Run command
eval "$COMMAND"
