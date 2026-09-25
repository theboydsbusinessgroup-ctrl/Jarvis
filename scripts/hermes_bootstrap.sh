#!/usr/bin/env bash
set -euo pipefail

# JARVIS-managed Hermes bootstrap.
# Run on a persistent Linux host or VM. Do not run inside the Vercel web app itself.

curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

echo
echo "Hermes installed."
echo "Next run: hermes setup"
echo "Choose Blank Slate first, then configure one model provider."
echo "Enable the API server in ~/.hermes/.env:"
echo "  API_SERVER_ENABLED=true"
echo "  API_SERVER_KEY=<strong-random-secret>"
echo "Start with: hermes gateway"
echo
echo "JARVIS then needs:"
echo "  HERMES_API_URL=https://<your-hermes-host>"
echo "  HERMES_API_KEY=<same-secret>"
echo "  HERMES_MODEL=hermes-agent"
