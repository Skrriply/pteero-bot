#!/bin/bash

cd /home/container || exit 1

echo "Running Python $(/usr/local/bin/python --version)"
echo "Running $(/bin/uv --version)"

echo ":/home/container$ ${STARTUP}"
eval ${STARTUP}
