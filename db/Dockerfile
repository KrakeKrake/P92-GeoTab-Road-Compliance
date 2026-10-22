
# Use Python 3.12
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Python settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install PostgreSQL client library
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy our Flask API code
COPY . .

# Flask API port
EXPOSE 5000

# Gunicorn instead of Flask's development server.
ENV API_WORKERS=2
CMD ["sh", "-c", "exec gunicorn --workers ${API_WORKERS:-2} --bind 0.0.0.0:5000 --access-logfile - --error-logfile - api:app"]