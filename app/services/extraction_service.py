import os
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

from app.models.schemas import (
    InvoiceSchema, 
    BOESchema, 
    AadhaarSchema, 
    PanSchema, 
    BillsSchema, 
    ChallanSchema
)

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY or API_KEY.strip() == "":
    raise ValueError("GEMINI_API_KEY is missing from environment variables or .env file.")

client = genai.Client(api_key=API_KEY)

SCHEMA_MAP = {
    "invoice": InvoiceSchema,
    "boe": BOESchema,
    "aadhaar": AadhaarSchema,
    "pan": PanSchema,
    "bills": BillsSchema,
    "challan": ChallanSchema
}

def extract_document_from_bytes(file_bytes: bytes, filename: str, doc_type: str = "invoice"):
    # Updated to active Flash models
    models_to_try = ['gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash']
    
    extension = filename.split(".")[-1].lower()
    mime_type = "application/pdf" if extension == "pdf" else f"image/{extension}"
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"

    target_schema = SCHEMA_MAP.get(doc_type.lower(), InvoiceSchema)
    last_exception = None

    for model_name in models_to_try:
        try:
            print(f"Sending file {filename} ({doc_type}) to Gemini using model: {model_name}...")

            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type,
                    ),
                    (
                        f"You are an expert enterprise document, ID, and multi-schema parser specializing in {doc_type.upper()} documents. "
                        f"Carefully extract all available fields for this specific {doc_type.lower()} document type. "
                        "Return the data precisely adhering to the provided JSON schema."
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=target_schema,
                    temperature=0.1,
                ),
            )
            
            if not response.text:
                print(f"[WARNING] Model {model_name} returned empty text. Trying next fallback model...")
                continue
            
            return target_schema.model_validate_json(response.text)
            
        except APIError as ae:
            print(f"[WARNING] API Error with model {model_name}: {ae}. Trying fallback...")
            last_exception = ae
            if getattr(ae, 'code', None) == 429:
                time.sleep(2)
            continue
        except ServerError as se:
            print(f"[WARNING] Model {model_name} unavailable (503). Trying fallback...")
            last_exception = se
            continue
        except Exception as e:
            print(f"[WARNING] Error with model {model_name}: {e}. Trying fallback...")
            last_exception = e
            continue

    print("--- GEMINI EXTRACTION ERROR ---")
    traceback.print_exc()
    raise last_exception or Exception("All Gemini models failed or quota was exceeded.")