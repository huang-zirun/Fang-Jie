#!/usr/bin/env bash
set -euo pipefail

chrome=""
for candidate in google-chrome google-chrome-stable /usr/bin/google-chrome "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    if command -v "$candidate" &>/dev/null || [[ -f "$candidate" ]]; then
        chrome="$candidate"
        break
    fi
done

if [[ -z "$chrome" ]]; then
    echo "Chrome not found" >&2
    exit 1
fi

userDataDir="$HOME/.intent-money/chrome-user-data"
mkdir -p "$userDataDir"

"$chrome" --remote-debugging-port=9222 --user-data-dir="$userDataDir" --no-first-run --no-default-browser-check &

echo "Chrome launched with remote debugging on port 9222"
echo "CDP debug URL: http://localhost:9222"
