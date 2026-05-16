#!/bin/bash

cd /home/container || exit 1

echo "Running Python $(/usr/local/bin/python --version)"
echo "Running $(/usr/local/bin/python -m uv --version)"

MODIFIED_STARTUP=$(eval echo $(echo ${STARTUP} | sed -e 's/{{/${/g' -e 's/}}/}/g'))
echo ":/home/container$ ${MODIFIED_STARTUP}"
eval exec ${MODIFIED_STARTUP}
