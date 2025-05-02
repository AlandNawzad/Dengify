# Use a slim Python image
FROM python:3.13-slim

# Install system dependencies (curl for thumbnails, ffmpeg for audio)
RUN apt-get update && \
    apt-get install -y curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy & install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot code
COPY . .

# Run the bot
CMD ["python", "main.py"]
