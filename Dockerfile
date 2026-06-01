# ─── Builder stage ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv==0.5.0

# Copy dependency specs
COPY pyproject.toml .
COPY README.md .

# Install production deps only (no dev extras)
RUN uv pip install --system --no-cache -e .

# ─── Runtime stage ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user
RUN groupadd -r vireo && useradd -r -g vireo vireo

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source
COPY --chown=vireo:vireo src/ ./src/

USER vireo

EXPOSE 8080

# Default: run CLI (override in Railway service config)
CMD ["python", "-m", "vireo_vigia.cli"]
