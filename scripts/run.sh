#!/usr/bin/env bash
set -euo pipefail

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Prefer project venv python if available
PYTHON="$ROOT_DIR/bin/python"
if [ ! -x "$PYTHON" ]; then
	PYTHON=python
fi

# Ensure src is on PYTHONPATH so `raspi` package is importable
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH+:$PYTHONPATH}"

# Forward any args to python module
if [ "$#" -gt 0 ]; then
	ARGS=("$@")
else
	ARGS=("-m" "raspi.main")
fi

exec "$PYTHON" "${ARGS[@]}" 2> >(grep -v -E "ALSA|jack|pulseaudio|Jack|Cannot" >&2)