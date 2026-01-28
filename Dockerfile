# --- Stage 1: Build Frontend ---
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend dependency definitions
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ .

# Build the application
# Vite builds to 'dist' by default
RUN npm run build

# --- Stage 2: Backend & Runtime ---
FROM python:3.12-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend

# Create data directory for SQLite
RUN mkdir -p /app/data

# Copy built frontend assets to a 'static' directory
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose port (Koyeb usually ignores EXPOSE but it's good practice)
EXPOSE 8000

# Run the application
# We use 'sh -c' to expand $PORT variable provided by Koyeb (defaults to 8000 if not set)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
