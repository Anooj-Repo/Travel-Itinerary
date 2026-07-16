import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GENAI_BASE_URL = "https://genailab.tcs.in/"
    GENAI_API_KEY = os.getenv("GENAI_API_KEY") or os.getenv("HF_TOKEN") or "YOUR_KEY_HERE"
    
    # Model Configurations
    CHAT_MODEL = "azure_ai/genailab-maas-Phi-4-reasoning"
    EXTRACTION_MODEL = "azure/genailab-maas-gpt-4o"
    EMBEDDING_MODEL = "azure/genailab-maas-text-embedding-3-large"
    
    # Flask Configuration
    FLASK_PORT = 5005
    FLASK_HOST = "0.0.0.0"
    DEBUG = True
