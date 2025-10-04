# Use slim Python image for smaller, faster builds
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Upgrade pip first
RUN python -m pip install --upgrade pip

# Install system dependencies (needed for some Python packages & ffmpeg)
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

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose default port (Railway sets $PORT automatically)
EXPOSE 8000

# Run your app with Gunicorn (Option 1: shell form to expand $PORT)
CMD gunicorn -w 4 -b 0.0.0.0:$PORT app:app
