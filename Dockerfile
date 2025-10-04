# Use slim Python image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Upgrade pip and install system dependencies
RUN python -m pip install --upgrade pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port (optional, for Docker documentation)
# EXPOSE 8000

# Start app dynamically using Render's $PORT
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:$PORT app:app"]
