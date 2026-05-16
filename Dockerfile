FROM python:3.14-slim

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    USER=container \
    HOME=/home/container

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# User configuration
RUN adduser --disabled-password --home /home/container container

# Entrypoint configuration
COPY --chown=container:container ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Runtime environment
USER container
WORKDIR /home/container

CMD ["/bin/bash", "/entrypoint.sh"]
