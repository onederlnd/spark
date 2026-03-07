#!/bin/bash

set -e

branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$branch" = "main" ]; then
    echo "== already on main"
    exit 1
fi

git checkout main
git pull origin main
git merge "$branch"
git push origin main
git branch -d $branch
git push origin --delete "$branch"

echo "== merged '$branch' into main and pushed"
echo "== start your next feature with: ./scripts/feature.sh"