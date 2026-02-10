"""Configuration management for the Insurance Claims Agent"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    def __init__(self):
        # Load config.json if exists
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, "r") as f:
                self.config_data = json.load(f)
        else:
            self.config_data = {}
    
    # API Configuration
    @property
    def openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY") or self.config_data.get("API_KEY", "")
    
    @property
    def openai_base_url(self) -> str:
        return os.getenv("OPENAI_BASE_URL") or self.config_data.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # Model Configuration
    @property
    def model_name(self) -> str:
        return os.getenv("MODEL_NAME", "gpt-4o-mini")
    
    @property
    def embedding_model(self) -> str:
        return os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # ChromaDB Configuration
    @property
    def chroma_persist_directory(self) -> str:
        return os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    
    @property
    def chroma_collection_name(self) -> str:
        return os.getenv("CHROMA_COLLECTION", "insurance_policies")
    
    # Data paths
    @property
    def policy_pdf_path(self) -> str:
        return os.getenv("POLICY_PDF_PATH", "./data/policy.pdf")
    
    @property
    def coverage_csv_path(self) -> str:
        return os.getenv("COVERAGE_CSV_PATH", "./data/coveragedata.csv")

# Global config instance
config = Config()
