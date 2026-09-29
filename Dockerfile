# ==============================================================================
# Sentinel OSINT & Intelligence Telegram Bot - Multi-Stage Production Dockerfile
# Optimized for minimal image size, non-root security execution, and fast builds.
# ==============================================================================

# Stage 1: Build Dependencies
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies for Pillow, ReportLab and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Minimal Production Runtime
FROM python:3.12-slim-bookworm AS runner

LABEL org.opencontainers.image.title="Sentinel Telegram OSINT Bot" \
      org.opencontainers.image.description="Advanced Telegram OSINT, Intelligence & Community Directory Engine" \
      org.opencontainers.image.version="2.5.0" \
      org.opencontainers.image.authors="anonymous020786@gmail.com" \
      org.opencontainers.image.source="https://github.com/anonymous020786-dotcom/UserInfoBotTelegram" \
      org.opencontainers.image.licenses="MIT"

# Set optimal Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    TZ=UTC

WORKDIR /app

# Install runtime libraries required for Pillow and ReportLab graphics rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder stage
COPY --from=builder /install /usr/local

# Create non-root system user and group for maximum container security
RUN groupadd -g 10001 sentinel && \
    useradd -u 10001 -g sentinel -s /bin/bash -m sentinel

# Copy project files into container
COPY --chown=sentinel:sentinel . .

# Ensure data directories exist and have proper permissions for sentinel user
RUN mkdir -p /app/data /app/data/avatars /app/data/exports && \
    chown -R sentinel:sentinel /app/data

# Switch to unprivileged security context
USER sentinel

# Container healthcheck probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python scripts/healthcheck.py || exit 1

# Graceful termination signal for aiogram & telethon
STOPSIGNAL SIGTERM

# Execute bot
CMD ["python", "main.py"]
