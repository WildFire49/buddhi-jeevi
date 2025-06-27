# ---- Builder Stage ----
# This stage installs build dependencies and Python packages
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    portaudio19-dev \
    libsndfile1 \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt requirements-db.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-db.txt

# Create cache directory and pre-download the sentence-transformer model
RUN mkdir -p /app/.embeddings_cache
ENV TRANSFORMERS_CACHE=/app/.embeddings_cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/.embeddings_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/app/.embeddings_cache')"

# ---- Final Stage ----
# This stage creates the final, lean production image
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for runtime
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    portaudio19-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN addgroup --system app && adduser --system --group app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the pre-downloaded model cache from builder stage
COPY --from=builder /app/.embeddings_cache /app/.embeddings_cache

# Copy application code
COPY . .

# Create directory for audio files and embeddings cache, set permissions for the non-root user
RUN mkdir -p temp_audio && \
    chown -R app:app /app temp_audio && \
    chown -R app:app /app/.embeddings_cache && \
    chmod -R 755 /app/.embeddings_cache

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.embeddings_cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/.embeddings_cache
ENV HF_HOME=/app/.embeddings_cache

# Expose both server and translation API ports
EXPOSE 8002
EXPOSE 8004

# Make the run_services.py script executable
RUN chmod +x run_services.py

# Switch to the non-root user
USER app

# Command to run both services
CMD ["python", "run_services.py"]
