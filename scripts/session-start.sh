#!/usr/bin/env bash
# Session start for Narrative Workbench cloud sessions.
#
# Runs from the SessionStart hook in .claude/settings.json on every cloud
# session, including resumed ones. Does nothing on a local machine.
#
# Sets up the Python engine's venv with NetworkX and pytest. System packages
# and Chromium come from the environment's setup script
# (scripts/cloud-env-setup.sh), which is cached between sessions.

set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
VENV="$PROJECT_DIR/.venv"

log() { echo "[session-start] $*" >&2; }

if [ ! -x "$VENV/bin/python" ]; then
  log "Creating Python venv at .venv"
  python3 -m venv "$VENV"
fi
if ! "$VENV/bin/python" -c "import networkx, pytest" >/dev/null 2>&1; then
  log "Installing NetworkX and pytest"
  "$VENV/bin/pip" install -q networkx pytest
fi

# Make the venv available to the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PATH=\"$VENV/bin:\$PATH\""
    echo "export VIRTUAL_ENV=\"$VENV\""
  } >> "$CLAUDE_ENV_FILE"
fi

log "Ready: $("$VENV/bin/python" --version), networkx $("$VENV/bin/python" -c 'import networkx; print(networkx.__version__)')"
