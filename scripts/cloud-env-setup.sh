#!/usr/bin/env bash
# Cloud environment setup script for Narrative Workbench.
#
# Paste this into the cloud environment's "Setup script" field at
# claude.ai/code. It runs as root before Claude Code starts, and the result is
# cached for later sessions if it finishes in about five minutes. This file is
# the version-controlled copy; it does not run on its own.
#
# Installs the Tauri v2 Linux build dependencies and headless Chromium for the
# spec's screenshot checks. Rust and Node 22 are pre-installed in the cloud
# image. The Python venv is set up per session by scripts/session-start.sh.
#
# Network: the Chromium download needs Playwright's hosts on the environment's
# allowlist (Custom access plus the default list, or Full).
#
# Limit: the cloud machine has no display, so it cannot open the Tauri desktop
# window. Check the real desktop app on the Mac.

set -uo pipefail

PLAYWRIGHT_VERSION=1.49.1

log() { echo "[cloud-env-setup] $*" >&2; }

# Tauri v2 Linux build dependencies (https://v2.tauri.app/start/prerequisites/)
log "Installing Tauri build dependencies"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  build-essential curl wget file pkg-config \
  libwebkit2gtk-4.1-dev libxdo-dev libssl-dev \
  libayatana-appindicator3-dev librsvg2-dev >/dev/null \
  || log "WARNING: apt install failed"

# Rust lint and format tools
if command -v rustup >/dev/null 2>&1; then
  rustup component add clippy rustfmt >/dev/null 2>&1 \
    || log "WARNING: rustup component add failed"
fi

# Headless Chromium. Once the front end has its own package.json, keep its
# Playwright version equal to PLAYWRIGHT_VERSION.
log "Installing headless Chromium (Playwright $PLAYWRIGHT_VERSION)"
npx -y "playwright@$PLAYWRIGHT_VERSION" install --with-deps chromium >/dev/null \
  || log "WARNING: Chromium install failed; check the environment's network allowlist"

log "Done: $(rustc --version 2>/dev/null), node $(node -v 2>/dev/null)"
exit 0
