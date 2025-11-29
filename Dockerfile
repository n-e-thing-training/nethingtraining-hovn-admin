# Dockerfile
FROM python:3.13-slim

# Install system deps if needed (e.g. for psycopg2 / playwright / etc)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose port (for local clarity; platforms can override)
EXPOSE 8000

# Start FastAPI via gunicorn + uvicorn worker
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]