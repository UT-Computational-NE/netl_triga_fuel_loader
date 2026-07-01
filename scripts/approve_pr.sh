#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 PR_NUMBER [MESSAGE]"
  echo "Environment: BOT_TOKEN may be set. If not, the script will try to extract a token from the origin remote URL."
  exit 1
}

if [ "$#" -lt 1 ]; then
  usage
fi

PR_NUMBER="$1"
MESSAGE="${2:-Approved via bot (manual request)}"

# Resolve token: prefer env var BOT_TOKEN, else attempt to parse from origin URL
TOKEN="${BOT_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  if remote_url=$(git remote get-url origin 2>/dev/null); then
    TOKEN=$(echo "$remote_url" | sed -n 's#.*://[^:]*:\([^@]*\)@.*#\1#p' || true)
  fi
fi

if [ -z "$TOKEN" ]; then
  echo "Error: no BOT_TOKEN environment variable and no token embedded in git remote URL." >&2
  exit 2
fi

# Determine repo in owner/repo form
if ! remote_url=$(git remote get-url origin 2>/dev/null); then
  echo "Error: cannot determine origin remote URL" >&2
  exit 3
fi
repo=$(echo "$remote_url" | sed -E 's#.*github.com[:/]+([^/]+/[^/]+)(\\.git)?$#\1#')
# strip trailing .git if present
repo=${repo%.git}
if [ -z "$repo" ]; then
  echo "Error: could not parse repo name from remote URL: $remote_url" >&2
  exit 4
fi

echo "Posting approval for PR #$PR_NUMBER on $repo as bot..."

resp=$(curl -sS -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "{\"body\": \"$MESSAGE\", \"event\": \"APPROVE\"}" \
  "https://api.github.com/repos/$repo/pulls/$PR_NUMBER/reviews")

echo "$resp"

echo "Done."
