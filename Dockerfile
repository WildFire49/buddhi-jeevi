# ---- Builder Stage ----
# This stage installs build dependencies and Python packages
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Final Stage ----
# This stage creates the final, lean production image
FROM python:3.10-slim

WORKDIR /app

# Create a non-root user and group
RUN addgroup --system app && adduser --system --group app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Create directory for audio files and set permissions for the non-root user
RUN mkdir -p temp_audio && chown -R app:app /app temp_audio

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8002

# Switch to the non-root user
USER app

# Command to run the application
CMD ["python", "server.py"]
