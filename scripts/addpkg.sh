#!/bin/bash

# scripts/addpkg.sh
# Usage: ./scripts/addpkg.sh

read -p "package name: " package

if [ -z "$package" ]; then
    echo "no package name provided."
    exit 1
fi

pip install "$package" --break-system-packages

if [ $? -eq 0 ]; then
    pip freeze | grep -i "$package" >> requirements.txt
    echo "== added '$package' to requirements.txt"
else
    echo "== install failed"
    exit 1
fi