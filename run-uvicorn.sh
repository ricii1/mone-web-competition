#!/usr/bin/env bash
# Run the Peta Pintar API with uvicorn (native/conda setup, see README.md).
#
# Usage: ./run-uvicorn.sh            # reload mode on 127.0.0.1:8000
#        PORT=8010 ./run-uvicorn.sh  # other port
#        HOST=0.0.0.0 ./run-uvicorn.sh
#        RELOAD=0 ./run-uvicorn.sh   # no auto-reload
#        CONDA_ENV=other ./run-uvicorn.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"
CONDA_ENV="${CONDA_ENV:-petapintar}"

# Activate the conda env (works even when conda is not initialised in this shell).
if ! command -v conda >/dev/null 2>&1; then
  for base in "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/miniforge3" "/opt/conda"; do
    if [ -f "$base/etc/profile.d/conda.sh" ]; then
      # shellcheck disable=SC1091
      . "$base/etc/profile.d/conda.sh"
      break
    fi
  done
fi
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate "$CONDA_ENV"
else
  echo "conda tidak ditemukan; memakai python/uvicorn dari PATH." >&2
fi

# Other toolchains (e.g. ROS) can leak pytest/python plugins through PYTHONPATH.
unset PYTHONPATH

cd "$ROOT/backend"

if [ ! -f .env ] && [ ! -f "$ROOT/.env" ]; then
  echo "File .env belum ada. Jalankan: cp .env.example .env (lihat README.md)." >&2
  exit 1
fi

ARGS=(app.main:app --host "$HOST" --port "$PORT")
if [ "$RELOAD" = "1" ]; then
  # A short graceful shutdown stops --reload from hanging on open WebSocket connections.
  ARGS+=(--reload --timeout-graceful-shutdown 2)
fi

echo "Peta Pintar API: http://$HOST:$PORT  (docs: http://$HOST:$PORT/docs)"
exec uvicorn "${ARGS[@]}"
