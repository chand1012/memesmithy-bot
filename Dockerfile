# Use uv base image with Python 3.14
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS base

# Set working directory
WORKDIR /app

# Install dependencies (transitive dependencies only, not the project itself)
# This layer will be cached separately from the project code
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the project files
COPY . /app

# Sync the project (install the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --compile-bytecode

# Use the virtual environment automatically
ENV PATH="/app/.venv/bin:$PATH"

# The bot requires DISCORD_TOKEN or BOT_TOKEN environment variable
# Set this when running the container:
# docker run -e DISCORD_TOKEN=your_token_here ...
# Or use a .env file mounted as a volume

# Run the bot
CMD ["python", "bot.py"]
