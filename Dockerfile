# --- Stage 1: Build Frontend ---
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

# Use lightweight cache and only necessary files
COPY frontend/package*.json ./
# --network-timeout 100000 helps with bad connections
RUN npm ci --quiet --no-progress 

COPY frontend/ .
# Limit memory for Node.js during build
ENV NODE_OPTIONS="--max-old-space-size=512"
RUN npm run build

# --- Stage 2: Backend & Runtime ---
FROM python:3.12-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and create data directory
COPY backend/ ./backend
RUN mkdir -p /app/data

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static

# Configure port
ENV PORT=8000
EXPOSE 8000

# Run the application
# We use 'sh -c' to expand $PORT variable provided by Koyeb (defaults to 8000 if not set)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
