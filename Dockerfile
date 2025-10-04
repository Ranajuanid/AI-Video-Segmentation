# Use Python 3.11 slim
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway assigns it dynamically)
EXPOSE 8000

# Use Railway's PORT environment variable
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
