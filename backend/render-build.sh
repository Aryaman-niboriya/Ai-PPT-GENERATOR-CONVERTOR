#!/usr/bin/env bash
# render-build.sh — Render calls this as the Build Command

set -o errexit  # exit on error

# Install system-level libs Pillow needs (jpeg, zlib, freetype, webp)
apt-get update -qq && apt-get install -y -qq \
  libjpeg-dev zlib1g-dev libfreetype6-dev libwebp-dev \
  2>/dev/null || true   # don't fail if apt isn't available (Render Docker)

# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt
