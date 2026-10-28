#!/usr/bin/env bash
# Bounded, non-force publication after concurrent repository updates.
set -euo pipefail
if [ "$#" -eq 0 ]; then echo "Expected output paths" >&2; exit 2; fi
git add -- "$@"
if git diff --cached --quiet; then
  echo "No data changes; nothing to publish."
  exit 0
fi
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git commit -m "data: refresh validated Power Atlas public source records"
for attempt in 1 2 3 4 5; do
  git fetch --quiet origin main
  if ! git rebase origin/main; then
    git rebase --abort || true
    echo "Conflicting data edits require review; no force-push attempted." >&2
    exit 1
  fi
  if git push origin HEAD:main; then
    echo "Data published on attempt ${attempt}."
    exit 0
  fi
  echo "Remote updated; retrying normal fetch/rebase/push (${attempt}/5)."
  sleep "$(( attempt * 2 ))"
done
echo "Bounded push retries exhausted; remote data preserved." >&2
exit 1
