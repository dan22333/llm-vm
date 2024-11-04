
# GCP LLM Deployment Project

This repository contains all the necessary files and instructions to deploy a Large Language Model (LLM) service on Google Cloud Platform (GCP). This setup includes provisioning cloud resources, handling authentication, caching, and managing the model deployment using Docker and FastAPI.

## Repository Structure

- **Dockerfile**: Specifies the Docker environment used to run the LLM service, including dependencies and setup.
- **cloud-init.yaml**: Configures the VM on GCP, setting up necessary environment configurations and installing essential packages upon instance startup.
- **cloudbuild.yaml**: GCP Cloud Build configuration file. This automates building the Docker image and pushing it to Google Container Registry.
- **Pipfile & Pipfile.lock**: Define Python dependencies for the project. `Pipfile` manages packages, and `Pipfile.lock` ensures consistency across installations.
- **cli.py**: The main FastAPI server code. It loads the LLM model, handles requests, and manages interactions with Hugging Face and Google Cloud Storage.
- **.env**: Contains environment variables for project configuration, including sensitive information like API keys. This file should be kept private.

## Prerequisites

1. **Google Cloud Platform**:
   - Google Cloud project with billing enabled.
   - Google Cloud Storage and Secret Manager API enabled.
   - Service account with sufficient permissions (Storage Admin, Secret Manager Accessor).
2. **Docker**: Installed locally to build and test the container.
3. **Pipenv**: For dependency management.

## Setup Instructions

### 1. Environment Variables

Set up the `.env` file in the root directory with the following keys:

```plaintext
PROJECT_ID=your-gcp-project-id
MODEL_ID=your-model-id-on-huggingface
BUCKET_NAME=your-gcs-bucket-name
CACHE_DIR=/mnt/disks/model-cache
SECRET_NAME=huggingface-token
```

### 2. Build the Docker Image

To build the Docker image locally, run:

```bash
docker build -t llm-service .
```

### 3. Deploying on GCP

1. **Provision Resources**:
   Use `cloud-init.yaml` for configuring VM resources on GCP. This YAML file will automatically set up necessary dependencies.

2. **Build and Push Image with Cloud Build**:

   Ensure `cloudbuild.yaml` is configured correctly with your GCP project settings. Then, trigger the build:

   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```

### 4. Running the Service

After the deployment is completed, the FastAPI server will be accessible. The endpoint `/generate/` accepts POST requests with a `text` field to generate responses.

Example request:

```json
{
  "text": "Hello, world!",
  "max_length": 100
}
```

## CLI Usage

The `cli.py` file contains the core FastAPI app with endpoints for interacting with the model. Key endpoints include:

- `/generate/`: Generates text based on the input prompt. Use this endpoint to interact with the model.

### Caching and Model Management

`cli.py` includes functionality for managing the LLM model cache. The model is stored in GCP and fetched as needed to optimize resource usage.

## Contribution

1. Clone the repository and make changes.
2. Ensure changes are consistent with the `.env` configuration.
3. Open a pull request with a description of your modifications.

---

Please reach out if you encounter any issues or have suggestions for improvement.
