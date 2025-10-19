from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Config(BaseModel):
    host: str = '127.0.0.1'
    port: int = 8000

    mistral_api_key: str = os.getenv('MISTRAL_API_KEY', '')
    mistral_embed_model: str = os.getenv('MISTRAL_EMBED_MODEL', 'mistral-embed')
    mistral_chat_model: str = os.getenv('MISTRAL_CHAT_MODEL', 'mistral-small-latest')
    mistral_ocr_model: str = os.getenv('MISTRAL_OCR_MODEL', 'mistral-ocr-latest')
    data_dir: str = os.getenv('DATA_DIR', 'data')

def get_config():
    return Config()
