FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build deps only for wheels that need them (scipy, numpy ship wheels).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY weather_alpha/pyproject.toml ./weather_alpha/pyproject.toml
COPY weather_alpha ./weather_alpha

RUN pip install -e ./weather_alpha \
    && pip install "py-clob-client>=0.17" "python-telegram-bot>=21"

EXPOSE 8000

# Scheduler binds 0.0.0.0:8000 and ticks the engine in the background.
CMD ["python", "-m", "weather_alpha.scheduler"]
