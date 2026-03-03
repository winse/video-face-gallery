# Base image with Python 3.10
FROM python:3.10-slim
ARG PREFER_GPU=1

# Set working directory inside the container
WORKDIR /app

# Install necessary system dependencies (ffmpeg is required for processing videos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to properly leverage Docker cache
COPY docker/requirements.txt /app/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ "$PREFER_GPU" = "1" ]; then \
      echo "Attempting GPU runtime install (onnxruntime-gpu)..." && \
      pip install --no-cache-dir "onnxruntime-gpu>=1.16.0" || \
      echo "onnxruntime-gpu install failed, keep CPU runtime (onnxruntime)."; \
    fi

# Copy source code folders
COPY engine/ /app/engine/
COPY modules/ /app/modules/
COPY tools/ /app/tools/
COPY web/ /app/web/

# Copy root python scripts
COPY *.py /app/

# Environment variables for the pipeline to map to Docker paths
ENV FFMPEG_PATH=ffmpeg \
    FFPROBE_PATH=ffprobe \
    USE_GPU=1 \
    PYTHONUNBUFFERED=1

# Expose port for the HTTP server
EXPOSE 8080

# Default command to run
# Use ENTRYPOINT to handle custom docker arguments or start scripts
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh
ENTRYPOINT ["/app/docker/entrypoint.sh"]
