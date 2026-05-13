FROM python:3.12-slim
WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY scrapers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway cron: runs once, scrapes, exits
CMD ["python", "scrapers/main.py"]
