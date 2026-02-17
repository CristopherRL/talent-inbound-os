FROM python:3.12-slim

WORKDIR /app

# System dependencies for asyncpg and bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Startup: run migrations then start server
CMD alembic upgrade head && \
    uvicorn talent_inbound.main:app --host 0.0.0.0 --port ${PORT:-8000}
