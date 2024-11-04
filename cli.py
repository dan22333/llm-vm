from fastapi import FastAPI, HTTPException
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
from google.cloud import storage, secretmanager
from dotenv import load_dotenv
import torch
import uvicorn
import os
import json
from pathlib import Path
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Configuration parameters
MODEL_ID = os.getenv("MODEL_ID")
PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")
CACHE_DIR = os.getenv("CACHE_DIR", "/mnt/disks/model-cache")
SECRET_NAME = os.getenv("secret-name", "huggingface-token")

logger.info(f"Starting service with MODEL_ID: {MODEL_ID}, BUCKET: {BUCKET_NAME}, CACHE_DIR: {CACHE_DIR}")

app = FastAPI()

def get_huggingface_token():
    try:
        logger.info("Accessing Secret Manager for HuggingFace token...")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        token = response.payload.data.decode("UTF-8").strip()
        logger.info("Successfully retrieved token from Secret Manager")
        return token
    except Exception as e:
        logger.error(f"Error accessing secret: {e}")
        raise

class ModelService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        logger.info("Initializing storage client...")
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.ensure_cache_dir()
        
        # Login to HuggingFace
        try:
            token = get_huggingface_token()
            logger.info("Logging into HuggingFace...")
            login(token=token)
            logger.info("Successfully authenticated with HuggingFace")
        except Exception as e:
            logger.error(f"Failed to authenticate with HuggingFace: {e}")
            raise

    def ensure_cache_dir(self):
        """Ensure cache directory exists"""
        try:
            Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache directory ensured at {CACHE_DIR}")
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
            raise

    def get_cache_path(self):
        """Get model-specific cache path"""
        model_name = MODEL_ID.replace('/', '--')
        return Path(CACHE_DIR) / model_name

    def is_model_cached(self):
        """Check if model is in local cache"""
        cache_path = self.get_cache_path()
        cached = cache_path.exists() and (cache_path / "config.json").exists()
        logger.info(f"Model cache status - {'found' if cached else 'not found'} at {cache_path}")
        return cached

    def download_from_bucket(self):
        """Download model from GCS bucket if available"""
        model_name = MODEL_ID.replace('/', '--')
        cache_path = self.get_cache_path()
        
        try:
            logger.info(f"Checking for model in bucket: {BUCKET_NAME}")
            blobs = list(self.bucket.list_blobs(prefix=f"models/{model_name}/"))
            if not blobs:
                logger.info("Model not found in bucket")
                return False

            logger.info(f"Downloading {len(blobs)} files from bucket...")
            for blob in blobs:
                local_path = cache_path / blob.name.split('/', 2)[2]
                local_path.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(local_path))
            logger.info("Model successfully downloaded from bucket")
            return True
        except Exception as e:
            logger.error(f"Error downloading from bucket: {e}")
            return False

    def upload_to_bucket(self):
        """Upload model to GCS bucket"""
        model_name = MODEL_ID.replace('/', '--')
        cache_path = self.get_cache_path()
        
        try:
            logger.info(f"Uploading model to bucket: {BUCKET_NAME}")
            file_count = 0
            for file_path in cache_path.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(cache_path)
                    blob = self.bucket.blob(f"models/{model_name}/{relative_path}")
                    blob.upload_from_filename(str(file_path))
                    file_count += 1
            logger.info(f"Successfully uploaded {file_count} files to bucket")
        except Exception as e:
            logger.error(f"Error uploading to bucket: {e}")
            raise

    def load_model(self):
        """Load model with caching strategy"""
        if self.model is not None:
            logger.info("Model already loaded, reusing existing model")
            return

        if not self.is_model_cached():
            logger.info("Model not found in cache")
            if not self.download_from_bucket():
                logger.info("Downloading model from HuggingFace")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    MODEL_ID,
                    cache_dir=self.get_cache_path()
                )
                logger.info("Tokenizer loaded from HuggingFace")
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    MODEL_ID,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    cache_dir=self.get_cache_path()
                )
                logger.info("Model loaded from HuggingFace")
                
                logger.info("Uploading model to bucket for future use")
                self.upload_to_bucket()
            else:
                logger.info("Loading model from bucket cache")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.get_cache_path(),
                    local_files_only=True
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.get_cache_path(),
                    torch_dtype=torch.float16,
                    device_map="auto",
                    local_files_only=True
                )
        else:
            logger.info("Loading model from local cache")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.get_cache_path(),
                local_files_only=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.get_cache_path(),
                torch_dtype=torch.float16,
                device_map="auto",
                local_files_only=True
            )
        
        logger.info(f"Model loaded successfully on device: {self.model.device}")

    def generate(self, text: str, max_length: int = 100) -> str:
        logger.info(f"Generating text with max_length={max_length}")
        self.load_model()
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
            logger.debug("Input tokenized and moved to device")

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_return_sequences=1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                logger.debug("Text generated successfully")

            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.info("Text decoded successfully")
            return result
        except Exception as e:
            logger.error(f"Error during text generation: {e}")
            raise

# Global model service instance
model_service = ModelService()

@app.post("/generate/")
async def generate_text(request: dict):
    try:
        input_text = request.get("text", "")
        max_length = request.get("max_length", 100)
        logger.info(f"Received generation request with max_length={max_length}")

        generated_text = model_service.generate(input_text, max_length)
        return {"generated_text": generated_text}

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))