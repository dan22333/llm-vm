# GCP LLM Deployment Project

Deploy and serve Large Language Models (LLMs) on Google Cloud Platform with automatic caching, GPU acceleration, and a REST API interface. This project provides a complete setup for running Hugging Face models as a service, with options for both public and gated models.

**Note:** See known bugs at the bottom 🪲

## Features
- 🚀 Fast deployment with single-command setup
- 💾 Multi-level caching (Local Disk → GCS Bucket → Hugging Face)
- 🔒 Secure secrets management for gated models
- 🎮 REST API interface with FastAPI
- 🖥️ GPU acceleration with NVIDIA T4/V100/A100
- 🐳 Containerized deployment with Docker
- ⚡ Interactive testing interface

## Prerequisites

1. **Google Cloud Platform Account**
   - Active project with billing enabled
   - APIs enabled:
     - Compute Engine
     - Cloud Build
     - Artifact Registry
     - Secret Manager
     - Cloud Storage

2. **Local Development Environment**
   - Google Cloud CLI (`gcloud`) installed and initialized
   - Docker installed (for local testing)
   - Python 3.12+ with pipenv

3. **Optional: Hugging Face Account**
   - Required only for gated models (e.g., Llama)
   - Access token saved in `../secrets/huggingface_token`

## Quick Start

1. **Clone and Configure**
   ```bash
   # Clone repository
   git clone git@github.com:dlops-io/llm-vm.git
   cd llm-vm

   # Copy and edit environment configuration
   cp .env.template .env
   # Edit .env with your desired configuration
   ```

2. **Build and Deploy**
   ```bash
   # Build container and push to Artifact Registry
   ./manage.sh build

   # Deploy VM with GPU and start service
   ./manage.sh deploy
   ```

3. **Test the Service**
   ```bash
   # Interactive testing interface
   ./test_llm.sh
   ```

## Configuration Guide

### Environment Variables (.env)
```bash
# Required Configuration
PROJECT_ID="your-gcp-project"     # Your GCP project ID
MODEL_ID="HuggingFaceTB/SmolLM2-1.7B-Instruct"  # Model to deploy

# Optional Configuration (defaults shown)
REGION="us-west4"                 # Must have GPU availability
ZONE="us-west4-b"                 # Specific zone in region
MACHINE_TYPE="n1-standard-1"      # VM instance type
GPU_TYPE="nvidia-tesla-t4"        # GPU accelerator type
PORT=8080                         # Service port
```

### Model Selection
- **Public Models**: Use any public Hugging Face model (e.g., `"HuggingFaceTB/SmolLM2-1.7B-Instruct"`)
- **Gated Models**: For models requiring authentication:
  1. Accept model terms on Hugging Face website
  2. Get access token from Hugging Face
  3. Save token to `../secrets/huggingface_token`

## Architecture

### Caching Strategy
1. First checks local disk cache
2. If not found, checks GCS bucket
3. Finally, downloads from Hugging Face
4. Automatically uploads to GCS for future use

### Components
- **FastAPI Server**: Handles HTTP requests and model interaction
- **GPU Acceleration**: Automatic NVIDIA driver setup
- **Cloud Storage**: Persistent model cache
- **Docker Container**: Isolated runtime environment

## Usage Examples

1. **Basic Generation**
   ```bash
   curl -X POST "http://<VM-IP>:8080/generate/" \
     -H "Content-Type: application/json" \
     -d '{"text": "What is machine learning?", "max_length": 100}'
   ```

2. **Interactive Session**
   ```bash
   ./test_llm.sh
   # Type prompts and get responses
   # Type 'q' to quit
   ```

## Management Commands

```bash
./manage.sh build              # Build and push container
./manage.sh deploy            # Create VM and start service
./manage.sh connect           # SSH into VM
./manage.sh teardown          # Remove all resources
```

## Monitoring and Maintenance

Check service status:
```bash
# SSH into VM
./manage.sh connect

# View service logs
sudo journalctl -u llm-service -f

# Check GPU status
nvidia-smi
```

## Troubleshooting

Common issues and solutions:
1. **GPU Not Available**: Check zone availability of GPU type
2. **Authentication Errors**: Verify service account permissions
3. **Model Download Failed**: Check HuggingFace token for gated models

## Known Bugs 🪲
The following are some implementation issues to be fixed in the near future.
- Issues authenticating with hugging_face token for gated models
- Model fails to load from bucket (but loading from Huggingface and saving to bucket works fine)
