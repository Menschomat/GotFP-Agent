# Use the official uv python slim image for lightweight builds
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv without installing the project itself
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and other necessary files
COPY README.md ./
COPY src/ ./src/

# Install the project itself
RUN uv sync --frozen --no-dev

# Expose port 8000 for the ADK Web UI
EXPOSE 8000

# Set environment variables path
ENV PYTHONPATH=/app/src

# Set the default command to run the interactive CLI
CMD ["uv", "run", "adk", "run", "src/text_adventure_bot"]
