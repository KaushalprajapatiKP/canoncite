#!/usr/bin/env bash
# Upload the staged CANONCITE payload to the HuggingFace Hub.
#
# Authentication: do NOT paste a token into a chat, a commit, or this file. Log in
# once, interactively, and the token is stored in your own keyring:
#
#     hf auth login
#
# or export it for a single shell, having read it from somewhere private:
#
#     export HF_TOKEN=$(cat ~/.hf_token)     # keep that file chmod 600
#
# Run from the repository root.
set -euo pipefail

ORG="${1:-}"
NAME="${2:-canoncite}"
PAYLOAD="release/hf/payload"

if [[ -z "$ORG" ]]; then
  echo "usage: bash release/hf/upload.sh <org-or-username> [dataset-name]" >&2
  echo "example: bash release/hf/upload.sh pralia-labs canoncite" >&2
  exit 2
fi

if [[ ! -d "$PAYLOAD" ]]; then
  echo "no payload at $PAYLOAD; run: python release/hf/build_hf.py" >&2
  exit 1
fi

REPO="$ORG/$NAME"

echo "about to upload:"
echo "  from   $PAYLOAD  ($(find "$PAYLOAD" -type f | wc -l | tr -d ' ') files, $(du -sh "$PAYLOAD" | cut -f1))"
echo "  to     https://huggingface.co/datasets/$REPO"
echo "  as     $(hf auth whoami 2>/dev/null || echo 'NOT LOGGED IN — run: hf auth login')"
echo
read -r -p "proceed? [y/N] " reply
[[ "$reply" == "y" || "$reply" == "Y" ]] || { echo "aborted"; exit 0; }

# --repo-type dataset is required; without it this would create a model repo.
hf repo create "$REPO" --repo-type dataset --private

echo
echo "uploading. the repo is created PRIVATE: verify it on the Hub, then make it"
echo "public from the settings page when you are satisfied."
hf upload "$REPO" "$PAYLOAD" . --repo-type dataset \
  --commit-message "CANONCITE v0: 10 corpora, 188,557 units, 622 items"

echo
echo "done: https://huggingface.co/datasets/$REPO"
echo "remaining steps, in order:"
echo "  1. check the dataset viewer renders all four configs"
echo "  2. confirm reviews/ contains no real annotator names"
echo "  3. flip to public in Settings when satisfied"
