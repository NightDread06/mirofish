FROM python:3.11

# 安装 Node.js （满足 >=18）及必要工具
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# 从 uv 官方镜像复制 uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# 先复制依赖描述文件以利用缓存
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# 安装依赖（Node + Python）
# Also install requirements.txt for ski dashboard dependencies (requests, APScheduler, Flask-Caching)
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen \
  && pip install --no-cache-dir -r /app/backend/requirements.txt 2>/dev/null || true

# 复制项目源码
COPY . .

EXPOSE 3000 5001

# 同时启动前后端（开发模式）
# The ski dashboard scheduler starts automatically with the Flask backend
CMD ["npm", "run", "dev"]