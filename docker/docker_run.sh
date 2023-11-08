#!/bin/bash
set -e
echo "Running script: $0"

# This scripts starts the docker project with the correct environment variables
# Will rebuild and start the project in detached mode, then follow the log output

# Get args
CONTAINER_DATA_DIR=$1
ENV_PATH=$2
USERNAME=$3
GROUPNAME=$4

# Get ids of the docker user
DOCKER_USER_ID=$(id -u "$USERNAME")
DOCKER_GROUP_ID=$(getent group "$GROUPNAME" | cut -d: -f3)

# Export env vars used in docker-compose configuration
export DOCKER_USER_ID DOCKER_GROUP_ID ENV_PATH CONTAINER_DATA_DIR

# -d: detached mode
# --build: rebuild image if changes to source code
# --force-recreate: ensures the container is restarted (even if no changes to source/config) instead of just attaching to the existing container
docker compose up -d --build --force-recreate && docker compose logs -f

# For running as interactive shell if you want to enter credentials manually (i.e. if not provided in .env file)
# docker compose run app
