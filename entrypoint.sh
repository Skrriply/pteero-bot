#!/bin/bash
set -e

cd /home/container || exit 1

echo "Using $(python --version)"
echo "Using $(uv --version)"

echo ":/home/container$ ${STARTUP}"
eval ${STARTUP}
