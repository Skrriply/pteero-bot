FROM python:3.14-slim

# Environment configuration
ARG USER_UID=998
ARG USER_GID=998
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
RUN groupadd -g ${USER_GID} ${USER} \
    && useradd -m -r -u ${USER_UID} -g ${USER} -d ${HOME} -s /bin/bash ${USER}

# Entrypoint configuration
COPY --chown=${USER}:${USER} --chmod=755 ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Runtime environment
USER ${USER}
WORKDIR ${HOME}

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
