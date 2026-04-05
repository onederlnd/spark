#!/bin/bash

set -e

branch=$(git rev-parse --abbrev-ref HEAD)

# ── Safety checks ──────────────────────────────────────────
if [ "$branch" = "main" ]; then
    echo "❌ Already on main — check out a feature branch first."
    exit 1
fi

echo ""
echo "🚀 About to merge '$branch' into main and deploy to production."
echo "   This will trigger an auto-deploy to Fly.io."
echo ""
echo "   Are you sure? (y/N)"
read confirm

if [ "$confirm" != "y" ]; then
    echo "== Aborted. Still on branch '$branch'."
    exit 0
fi

# ── Switch to main and pull latest ─────────────────────────
echo "== Switching to main and pulling latest..."
git checkout main
git pull origin main

# ── Merge feature branch ────────────────────────────────────
echo "== Merging '$branch'..."
if ! git merge "$branch"; then
    echo ""
    echo "❌ Merge conflict detected!"
    echo "   Resolve the conflicts manually, then run:"
    echo "     git add ."
    echo "     git commit"
    echo "     git push origin main"
    echo "     git branch -d $branch"
    echo "     git push origin --delete $branch"
    exit 1
fi

# ── Push to main ────────────────────────────────────────────
echo "== Pushing to main (auto-deploy will start)..."
git push origin main

# ── Clean up branch ─────────────────────────────────────────
echo "== Cleaning up branch '$branch'..."
git branch -d "$branch"
git push origin --delete "$branch"

# ── Archive notes ────────────────────────────────────────────
if [ -f "NOTES.md" ]; then
    safe_branch=$(echo "$branch" | tr '/' '-')
    mkdir -p "NOTES-archive"
    cp NOTES.md "NOTES-archive/NOTES-$safe_branch.md"
    echo "== Notes archived to NOTES-archive/NOTES-$safe_branch.md"
fi

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "✅ '$branch' merged into main and pushed."
echo "   🔍 Watch your deploy at: https://fly.io/apps/social-platform/monitoring"
echo "   🌐 Live at: https://go-spark.app"
echo ""
echo "== Start your next feature with: ./scripts/feature.sh"