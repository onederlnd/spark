#!/bin/bash
# dev workflow: test -> lint -> commit -> push

set -e

SKIP_TESTS=false
if [[ "$1" == "--skip" ]]; then
    SKIP_TESTS=true
fi
. .venv/bin/activate

echo "== running..."
if [ "$SKIP_TESTS" = false ]; then
    echo "== running tests..."
    pytest tests/
else
    echo "== skipping tests..."
fi

echo "== linting..."
flake8 app/ --max-line-length=120 --ignore=W503

echo "== staging changes..."
git add .
git status
echo ""
read -p "commit message: " msg

if [ -z "$msg" ]; then
    echo "== commit message required"
    exit 1
fi

git commit -m "$msg"

branch=$(git rev-parse --abbrev-ref HEAD)
git push -u origin "$branch"

echo "== shipped on branch: $branch"

if [ "$branch" != "main" ]; then
    echo "== open a PR at: https://github.com/onederlnd/devstack/compare/$branch"
fi