#!/usr/bin/env bash
set -euo pipefail

# JARVIS-managed Hermes bootstrap.
# Run only on a persistent Linux host or VM, never in the Vercel web app.
# The official installer is not executed unless its reviewed SHA-256 is supplied.

installer_url="https://hermes-agent.nousresearch.com/install.sh"
expected_sha256="${HERMES_INSTALLER_SHA256:-}"

if [[ -z "${expected_sha256}" ]]; then
  echo "Refusing to execute an unverified remote installer." >&2
  echo "Review the official installer, calculate its SHA-256, then rerun with:" >&2
  echo "  HERMES_INSTALLER_SHA256=<reviewed-sha256> scripts/hermes_bootstrap.sh" >&2
  exit 2
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT
installer_path="${tmp_dir}/hermes-install.sh"

curl --fail --silent --show-error --location --proto '=https' --tlsv1.2   "${installer_url}" --output "${installer_path}"

actual_sha256="$(sha256sum "${installer_path}" | awk '{print $1}')"
if [[ "${actual_sha256}" != "${expected_sha256}" ]]; then
  echo "Hermes installer checksum mismatch; nothing was executed." >&2
  echo "Expected: ${expected_sha256}" >&2
  echo "Actual:   ${actual_sha256}" >&2
  exit 3
fi

bash "${installer_path}"

echo
echo "Hermes installed from a checksum-verified installer."
echo "Next run: hermes setup"
echo "Choose Blank Slate first, then configure one model provider."
echo "Enable the API server in ~/.hermes/.env:"
echo "  API_SERVER_ENABLED=true"
echo "  API_SERVER_KEY=<strong-random-secret>"
echo "Start with: hermes gateway"
echo
echo "JARVIS then needs:"
echo "  HERMES_ENABLED=true"
echo "  HERMES_API_URL=https://<your-hermes-host>"
echo "  HERMES_API_KEY=<same-secret>"
echo "  HERMES_MODEL=hermes-agent"
