# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (Railway automatically sets $PORT)
ENV PORT 8080
EXPOSE $PORT

# Command to run the app using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
