import os
import sys
import importlib.util

# 1. Metaprogramming Hook: Force 'app' to resolve to the 'app/' directory package
# This prevents Python from colliding the root 'app.py' launcher with the 'app' package.
script_dir = os.path.dirname(os.path.abspath(__file__))
app_package_init = os.path.join(script_dir, "app", "__init__.py")

spec = importlib.util.spec_from_file_location("app", app_package_init)
app_module = importlib.util.module_from_spec(spec)
sys.modules["app"] = app_module
spec.loader.exec_module(app_module)

# Now proceed with normal imports
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from app.config.settings import Config
from app.services.rag_service import RAGService

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="KrishiKantho AI Knowledge Ingestion Pipeline")
    parser.add_argument(
        "--file", 
        type=str, 
        help="Path to a specific PDF or TXT file to ingest"
    )
    parser.add_argument(
        "--crop", 
        type=str, 
        default="general", 
        help="Crop tag/category for the ingested document (e.g. rice, wheat, tomato)"
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset the ChromaDB database before ingesting"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Initialize settings and folders
    Config.init_app()
    rag_service = RAGService()
    
    # Reset vector store if requested
    if args.reset:
        logger.info("Resetting ChromaDB database...")
        rag_service.vector_store.reset()
        logger.info("Database reset complete.")

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
            
        ingest_single_file(file_path, args.crop, rag_service)
    else:
        # Ingest all files in data/documents
        doc_dir = Path(Config.KNOWLEDGE_BASE_DIR)
        logger.info(f"Scanning directory for documents: {doc_dir.resolve()}")
        
        supported_extensions = [".pdf", ".txt"]
        files = [f for f in doc_dir.iterdir() if f.is_file() and f.suffix.lower() in supported_extensions]
        
        if not files:
            logger.info("No documents found in data/documents/ directory. Run with --file to ingest a specific file.")
            logger.info("Default seed guidelines are automatically loaded when starting the application.")
            return
            
        for file_path in files:
            # Guess crop tag based on filename
            crop = "general"
            filename_lower = file_path.name.lower()
            for c in ["rice", "wheat", "tomato", "jute", "poultry", "fish"]:
                if c in filename_lower:
                    crop = c
                    break
                    
            ingest_single_file(file_path, crop, rag_service)

def ingest_single_file(file_path: Path, crop: str, rag_service: RAGService):
    ext = file_path.suffix.lower()
    logger.info(f"Ingesting file: {file_path.name} (Crop: {crop})")
    
    if ext == ".pdf":
        success = rag_service.ingest_pdf(str(file_path), crop_tag=crop)
        if success:
            logger.info(f"Successfully ingested PDF: {file_path.name}")
        else:
            logger.error(f"Failed to ingest PDF: {file_path.name}")
            
    elif ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            rag_service.ingest_text(text, file_path.name, crop_tag=crop)
            logger.info(f"Successfully ingested TXT: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to read TXT: {file_path.name}. Error: {e}")
            
    else:
        logger.warning(f"Unsupported file type: {file_path.name}")

if __name__ == "__main__":
    main()
