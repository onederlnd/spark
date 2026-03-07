# dev workflow: test -> lint -> commit -> push

#!/bin/bash


set -e

. .venv/bin/activate

echo "== running tests..."
pytest tests/ -v

echo "== linting..."
flake8 app/ --max-line-length=100 --ignore=E501,W503

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

# moved here — no longer blocks feature branches
branch=$(git rev-parse --abbrev-ref HEAD)
git push -u origin "$branch"

echo "== shipped on branch: $branch"

# notify instead of exit
if [ "$branch" != "main" ]; then
    echo "== open a PR at: https://github.com/onederlnd/devstack/compare/$branch"
fi