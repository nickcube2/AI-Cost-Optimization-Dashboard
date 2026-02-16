FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source.
COPY . /app

# Create and use an unprivileged user.
RUN useradd --create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Default to the web dashboard; override command for CLI scripts.
CMD ["python", "app.py"]
