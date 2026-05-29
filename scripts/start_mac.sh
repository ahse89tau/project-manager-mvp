#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting pm-app container..."
docker compose up -d --build
echo "pm-app is running at http://localhost:8000"
