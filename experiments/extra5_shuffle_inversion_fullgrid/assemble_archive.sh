#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
archive="EXTRA5_ShuffleInvariant_Exact_Inversion_2026_10_30.zip"
cat archive_parts/part_*.b64 | base64 --decode > "$archive"
printf '%s  %s\n' 'c3f02f8c96fe59c34b61e521bf3613a68d531aecb5e02c8dddef726323b37712' "$archive" | sha256sum --check -
unzip -tq "$archive"
echo "Restored the verified 83-file research archive: $archive"
