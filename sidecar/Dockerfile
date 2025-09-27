# Galaxy Infrastructure Sidecar
# Provides standardized Galaxy endpoints for unmanaged infrastructure services
FROM python:3.11-slim

# Labels for Galaxy platform
LABEL service.name="infra-smoke-postgres-sidecar" \
      service.tier="infra" \
      service.workload="sidecar" \
      service.team="team3" \
      galaxy.io/managed-by="galaxy" \
      galaxy.io/sidecar-for="infra-smoke-postgres"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Galaxy sidecar application
COPY galaxy_sidecar.py ./

# Create non-root user for security
RUN useradd -m -u 1000 sidecar && chown -R sidecar:sidecar /app
USER sidecar

# Expose Galaxy standard port
EXPOSE 3000

# Galaxy health check for the sidecar itself
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f -H "X-Service-Name: infra-smoke-postgres-sidecar" -H "X-Service-Team: team3" -H "X-Service-Tier: infra" http://localhost:3000/health || exit 1

# Run Galaxy sidecar
CMD ["python", "galaxy_sidecar.py"]