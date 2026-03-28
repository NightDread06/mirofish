# Stage 1: Build the Vue frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy dependency manifests first to leverage layer caching
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/

RUN npm ci && npm ci --prefix frontend

# Copy frontend source and build for production
COPY frontend/ ./frontend/
RUN npm run build --prefix frontend

# Stage 2: Production Python image
FROM python:3.11-slim

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Install Python dependencies
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen --no-dev && uv pip install gunicorn

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend from the builder stage
COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

EXPOSE 5001

# Run Flask via gunicorn (production WSGI server)
CMD ["backend/.venv/bin/gunicorn", "--workers", "2", "--bind", "0.0.0.0:5001", "--chdir", "/app/backend", "wsgi:app"]