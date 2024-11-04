FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu24.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Install Pipenv in virtual environment
RUN pip install pipenv

# Install Google Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-sdk \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory and copy application code
WORKDIR /app
COPY . .

# Install dependencies
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --ignore-pipfile

# Create cache directory
RUN mkdir -p /mnt/disks/model-cache && chmod 777 /mnt/disks/model-cache

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application
CMD ["pipenv", "run", "uvicorn", "cli:app", "--host", "0.0.0.0", "--port", "8080"]
