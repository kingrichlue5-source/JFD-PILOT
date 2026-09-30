# Optional build strategy for Sevalla (Settings > Build strategy > Dockerfile).
# Default remains Nixpacks via nixpacks.toml + Procfile.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=jfd_hms.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

# Sevalla injects PORT; start.sh falls back to 8000 locally.
EXPOSE 8080

CMD ["bash", "start.sh"]
