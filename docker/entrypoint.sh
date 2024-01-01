#!/bin/bash

echo "Running as user: $(whoami) $(id -u):$(id -g)"

# Prevent running as root unless explicitly allowed
if [ "$1" != "--allow-root" ]; then
    # Ensure non root user
    if [ "$(id -u)" -eq 0 ] || [ "$(id -G | grep -w 0)" ]; then
        echo 'Error: The container must not run as root or be part of root group.'
        exit 1
    fi
fi

# Run the main script
poetry run python main.py
