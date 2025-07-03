# Use official Python runtime as base image
FROM python:3.10-slim

# Build argument to choose PyTorch version
ARG CUDA_VERSION=cu126
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/${CUDA_VERSION}

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install all dependencies together to avoid conflicts
RUN pip install --no-cache-dir \
    --extra-index-url ${TORCH_INDEX_URL} \
    torch torchvision torchaudio \
    transformers>=4.30.0 \
    datasets>=2.10.0 \
    accelerate>=0.20.0 \
    tokenizers>=0.13.0 \
    sentencepiece>=0.1.99 \
    pillow>=9.0.0 \
    numpy>=1.21.0 \
    requests>=2.25.0 \
    scipy>=1.7.0 \
    protobuf>=3.20.0

# Copy the application files
COPY image-mask-server.py .

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set up Hugging Face cache directory
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p $HF_HOME

# Expose port for the HTTP server
EXPOSE 8000

# Default command - run the image segmentation server
CMD ["python", "image-mask-server.py"]