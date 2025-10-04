# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        cmake \
        python3-dev \
        git \
        curl \
        wget \
        libffi-dev \
        libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Railway
ENV PORT 8080

# Expose the port
EXPOSE 8080

# Run the application with gunicorn
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
