# ============================
# 1) FRONTEND BUILD STAGE
# ============================
FROM node:18 AS frontend

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend/ .
RUN npm run build   # <--- creates /frontend/dist/

# ============================
# 2) BACKEND BUILD STAGE
# ============================
FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy the built frontend into /app/frontend/dist
COPY --from=frontend /frontend/dist ./frontend/dist

# Expose port
ENV PORT=8080
EXPOSE 8080

# Start FastAPI
CMD ["sh", "-c", "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT}"]
