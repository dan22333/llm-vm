
# GCP LLM Deployment Project

This repository contains all the necessary files and instructions to deploy a Large Language Model (LLM) service on Google Cloud Platform (GCP). This setup includes provisioning cloud resources, handling authentication, caching, and managing the model deployment using Docker and FastAPI.

## Repository Structure

- **Dockerfile**: Specifies the Docker environment used to run the LLM service, including dependencies and setup.
- **cloud-init.yaml**: Configures the VM on GCP, setting up necessary environment configurations and installing essential packages upon instance startup.
- **cloudbuild.yaml**: GCP Cloud Build configuration file. This automates building the Docker image and pushing it to Google Container Registry.
- **Pipfile & Pipfile.lock**: Define Python dependencies for the project. `Pipfile` manages packages, and `Pipfile.lock` ensures consistency across installations.
- **cli.py**: The main FastAPI server code. It loads the LLM model, handles requests, and manages interactions with Hugging Face and Google Cloud Storage.
- **manage.sh**: script with functions for building & pushing the container image as well as deploying, connecting via SSH, and tearing down the infrastructure on GCP.
- **test_llm.sh**: Send a prompt to the LLM's endpoint.
- **.env**: Contains environment variables for project configuration, including sensitive information like API keys. This file should be kept private.

## Prerequisites

1. **Google Cloud Platform**:
   - Google Cloud project with billing enabled.
   - Google Cloud Storage and Secret Manager API enabled.
   - Service account with sufficient permissions (Storage Admin, Secret Manager Accessor).
2. **Google Cloud CLI**: For `gloud` commands for interacting with GCP.
3. **Docker**: Installed locally to build and test the container.
4. **Pipenv**: For dependency management.

## Setup Instructions

### 1. Environment Variables

Set up the `.env` file in the root directory with the following keys:

```plaintext
PROJECT_ID=ac215-project
MODEL_ID="meta-llama/Llama-3.2-3B-Instruct" # Any LLM from Huggingface
#MODEL_ID=""
BUCKET_NAME=huggingface-llm
REGION=us-west4 # Region and zone must have your GPU/Machine available
ZONE=us-west4-b
INSTANCE_NAME=llama3-model-instance
DISK_NAME=model-cache-disk
DISK_SIZE=200GB
MACHINE_TYPE=n1-standard-1
GPU_TYPE=nvidia-tesla-t4
REPO_NAME=llama3-repo
IMAGE_NAME=llama3-model
SA_NAME=llm-runtime-sa
PORT=8080
```

**Note:** If you want to use a model like Llama3 which requires aproved access, you must first create a Huggingface account, aggree to the model's terms of service, wait for approval, and finally add your access token to `../secrets/huggingface_token`

There are many other models such as `'HuggingFaceTB/SmolLM2-1.7B-Instruct'` which you can pull without any specal permissions.

### 2. Build & Push Docker Image

To build the Docker image with Google Cloud Build, and psuh to the Artifact Registry:

```bash
./manage build
```

### 3. Deploying on GCP

**Provision Resources**:
To create a GCP VM running the image in the AR use:
`./manage deploy`
   
This makes use of `cloud-init.yaml` for configuring the base VM on startup, including the installation of NVIDIA drivers and running the container with appropriate flags.

### 4. Running the Service

After the deployment is completed, the FastAPI server will be accessible. The endpoint `/generate/` accepts POST requests with a `text` field to generate responses.

Example request:

```json
{
  "text": "Hello, world!",
  "max_length": 100
}
```
You can use the provided `./test_llm` script to send the endpoint a prompt.
**Note:** The current CLI implementation only loads the model upon the first received prompt...

## CLI Usage

The `cli.py` file contains the core FastAPI app with endpoints for interacting with the model. Key endpoints include:

- `/generate/`: Generates text based on the input prompt. Use this endpoint to interact with the model.

### Caching and Model Management

`cli.py` includes functionality for managing the LLM model cache. The model is stored in GCP and fetched as needed to optimize resource usage.
