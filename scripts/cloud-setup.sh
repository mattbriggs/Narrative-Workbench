#!/usr/bin/env bash
# Cloud session setup for Narrative Workbench.
#
# Runs at the start of each Claude Code cloud session (SessionStart hook in
# .claude/settings.json). Does nothing on a local machine.
#
# Installs: Rust, Node, Python + NetworkX, Tauri v2 Linux build dependencies,
# and headless Chromium for the spec's screenshot checks.
#
# Limit: the cloud machine has no display, so it cannot open the Tauri desktop
# window. It can build and test the Rust and Python parts and serve the web
# front end to headless Chromium. Check the real desktop app on the Mac.
#
# Safe to rerun: each step skips work that is already done.

set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
NODE_MAJOR=22
PLAYWRIGHT_VERSION=1.49.1

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  SUDO="sudo"
fi

log() { echo "[cloud-setup] $*" >&2; }

# Tauri v2 Linux build dependencies (https://v2.tauri.app/start/prerequisites/)
TAURI_PKGS=(
  build-essential curl wget file pkg-config
  libwebkit2gtk-4.1-dev libxdo-dev libssl-dev
  libayatana-appindicator3-dev librsvg2-dev
)
missing=()
for pkg in "${TAURI_PKGS[@]}"; do
  dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
done
if [ "${#missing[@]}" -gt 0 ]; then
  log "Installing system packages: ${missing[*]}"
  $SUDO apt-get update -qq
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq "${missing[@]}" >/dev/null
fi

# Rust
if ! command -v cargo >/dev/null 2>&1 && [ ! -x "$HOME/.cargo/bin/cargo" ]; then
  log "Installing Rust"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --profile minimal --component clippy,rustfmt >/dev/null
fi
export PATH="$HOME/.cargo/bin:$PATH"

# Node
node_major() { node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/'; }
if [ "$(node_major || echo 0)" -lt "$NODE_MAJOR" ] 2>/dev/null; then
  log "Installing Node $NODE_MAJOR"
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | $SUDO -E bash - >/dev/null
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq nodejs >/dev/null
fi

# Python engine: project venv with NetworkX and pytest
VENV="$PROJECT_DIR/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  log "Creating Python venv at .venv"
  python3 -m venv "$VENV"
fi
if ! "$VENV/bin/python" -c "import networkx, pytest" >/dev/null 2>&1; then
  log "Installing NetworkX and pytest"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q networkx pytest
fi

# Headless Chromium for screenshots. Once the front end has its own
# package.json, keep its Playwright version equal to PLAYWRIGHT_VERSION.
if ! ls "$HOME/.cache/ms-playwright" 2>/dev/null | grep -q '^chromium'; then
  log "Installing headless Chromium (Playwright $PLAYWRIGHT_VERSION)"
  npx -y "playwright@$PLAYWRIGHT_VERSION" install --with-deps chromium >/dev/null
fi

# Make the tools available to the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PATH=\"$VENV/bin:$HOME/.cargo/bin:\$PATH\""
    echo "export VIRTUAL_ENV=\"$VENV\""
  } >> "$CLAUDE_ENV_FILE"
fi

log "Ready: $(rustc --version), node $(node -v), $("$VENV/bin/python" --version), networkx $("$VENV/bin/python" -c 'import networkx; print(networkx.__version__)')"
