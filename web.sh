#!/bin/bash
set -e

cd "$(dirname "$0")"
source .venv/bin/activate
export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib/python3.12/site-packages/nvidia/cublas/lib:${LD_LIBRARY_PATH:-}"
python server.py
