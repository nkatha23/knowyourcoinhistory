# ── Stage 1: build the React frontend ──────────────────────────────────────
FROM node:20-alpine AS frontend

WORKDIR /app/web

# Install dependencies first so Docker can cache this layer.
# Only re-runs when package*.json changes, not on every source edit.
COPY web/package*.json ./
RUN npm ci

COPY web/ ./
RUN npm run build
# Output: /app/web/dist


# ── Stage 2: Python backend + bundled frontend ──────────────────────────────
FROM python:3.11-slim AS app

WORKDIR /app

# Install Python dependencies before copying source so this layer is cached.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY kycc/ ./kycc/
COPY main.py ./

# Bring in the compiled frontend from stage 1
COPY --from=frontend /app/web/dist ./web/dist

# SQLite label store lives under /data.
# Mount a named volume here to persist labels across container restarts.
VOLUME ["/data"]

EXPOSE 5050

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "kycc.server:create_app()"]
