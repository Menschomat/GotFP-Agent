FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Avoid prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Update system packages and install prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    gnupg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud CLI (gcloud) for easy authentication
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update -y \
    && apt-get install google-cloud-cli -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
