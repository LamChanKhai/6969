#!/bin/bash
set -e
cd "$(dirname "$0")"
{
  cat shell-head.html
  for f in sections/*.html; do cat "$f"; done
  cat shell-foot.html
} > deck.html
echo "[ok] deck.html ($(wc -c < deck.html) bytes, $(grep -c '<section class="slide' deck.html) slides)"
