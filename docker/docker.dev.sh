#!/bin/bash
set -e
echo "Running script: $0"

# The purpose of this script is being able to run and test the docker project locally.
# Working dir is assumed to be in the docker folder of the project
# Location of .env and the creation of the container data directory is assumed to be in the parent of the project root directory (avoids committing secrets to git by accident)

# Set paths with above assumptions
CONTAINER_DATA_DIR="../../data"
ENV_PATH="../../.env"

# Local user to run the container as
USERNAME="garmin-health-bot"
GROUPNAME=$USERNAME

# Uncomment to use setup script used in prod (set up user, dir, permissions). May not be relevant/necessary in dev
# ./docker_setup.sh $CONTAINER_DATA_DIR $ENV_PATH $USERNAME $GROUPNAME

./docker_run.sh $CONTAINER_DATA_DIR $ENV_PATH $USERNAME $GROUPNAME