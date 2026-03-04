# CUDA 12 runtime + cuDNN (required by onnxruntime-gpu CUDA provider)
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ARG APT_MIRROR=mirrors.ustc.edu.cn
ARG PIP_INDEX_URL=https://pypi.mirrors.ustc.edu.cn/simple/
ARG PIP_TRUSTED_HOST=pypi.mirrors.ustc.edu.cn

# Set working directory inside the container
WORKDIR /app

# Use USTC mirror for Ubuntu apt repository to speed up package download
RUN sed -i "s|http://archive.ubuntu.com|https://${APT_MIRROR}|g; s|http://security.ubuntu.com|https://${APT_MIRROR}|g; s|archive.ubuntu.com|${APT_MIRROR}|g; s|security.ubuntu.com|${APT_MIRROR}|g" /etc/apt/sources.list || true

# Install necessary system dependencies (ffmpeg is required for processing videos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    ca-certificates \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Make `python` command available consistently
RUN ln -sf /usr/bin/python3 /usr/local/bin/python && \
    ln -sf /usr/bin/pip3 /usr/local/bin/pip

# Copy requirements file first to properly leverage Docker cache
COPY docker/requirements.txt /app/requirements.txt

# Install python dependencies
RUN pip config set global.index-url "${PIP_INDEX_URL}" && \
    pip config set global.trusted-host "${PIP_TRUSTED_HOST}" && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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
