# --- Stage 1: Build Frontend ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Используем легкий кэш и только необходимые файлы
COPY frontend/package*.json ./
# --network-timeout 100000 помогает при плохом соединении
RUN npm ci --quiet --no-progress 

COPY frontend/ .
# Ограничиваем память для Node.js во время билда
ENV NODE_OPTIONS="--max-old-space-size=512"
RUN npm run build

# --- Stage 2: Backend & Runtime ---
FROM python:3.12-slim
WORKDIR /app

# Установка зависимостей бэкенда
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код и создаем папку для БД
COPY backend/ ./backend
RUN mkdir -p /app/data

# Забираем билд фронта
COPY --from=frontend-builder /app/frontend/dist ./static

# Настройка порта
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]

# Run the application
# We use 'sh -c' to expand $PORT variable provided by Koyeb (defaults to 8000 if not set)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
