# app/repositories/document_store.py
import os
import re
from pathlib import Path
from typing import List, Dict, Any
from app.config.settings import Config
from app.models.rag_document import RAGDocument

class DocumentStore:
    def __init__(self, doc_dir: Path = None):
        self.doc_dir = doc_dir or Config.KNOWLEDGE_BASE_DIR
        self.doc_dir.mkdir(parents=True, exist_ok=True)

    def load_documents(self) -> List[RAGDocument]:
        """Loads and chunks all text and PDF files inside the documents directory."""
        documents = []
        if not self.doc_dir.exists():
            return documents

        for file_path in self.doc_dir.iterdir():
            if file_path.suffix.lower() == ".txt":
                documents.extend(self._load_txt(file_path))
            elif file_path.suffix.lower() == ".pdf":
                documents.extend(self._load_pdf(file_path))
        
        return documents

    def _load_txt(self, file_path: Path) -> List[RAGDocument]:
        """Loads a text file and chunks it."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self._chunk_text(content, file_path.name, "txt")
        except Exception as e:
            print(f"Error reading TXT {file_path.name}: {e}")
            return []

    def _load_pdf(self, file_path: Path) -> List[RAGDocument]:
        """Loads a PDF file and chunks it. Safely falls back if pdf libraries are not installed."""
        try:
            # Try importing PyPDF2 or pdfplumber
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                chunks = []
                for page_idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        chunks.extend(self._chunk_text(text, file_path.name, "pdf", page_number=page_idx + 1))
                return chunks
            except ImportError:
                # Try fallback standard pypdf
                try:
                    import PyPDF2
                    with open(file_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        chunks = []
                        for page_idx in range(len(reader.pages)):
                            text = reader.pages[page_idx].extract_text() or ""
                            if text.strip():
                                chunks.extend(self._chunk_text(text, file_path.name, "pdf", page_number=page_idx + 1))
                        return chunks
                except ImportError:
                    print(f"PDF extraction library (pypdf/PyPDF2) not installed. Cannot parse {file_path.name}")
                    return []
        except Exception as e:
            print(f"Error reading PDF {file_path.name}: {e}")
            return []

    def _chunk_text(self, text: str, source_name: str, doc_type: str, page_number: int = 1, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[RAGDocument]:
        """Splits text into overlapping chunks and labels metadata."""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Infer crop/disease from source_name or content
        crop = "general"
        disease = "general"
        
        name_lower = source_name.lower()
        if "rice" in name_lower or "ধান" in name_lower:
            crop = "rice"
        elif "wheat" in name_lower or "গম" in name_lower:
            crop = "wheat"
        elif "tomato" in name_lower or "টমেটো" in name_lower:
            crop = "tomato"
        elif "jute" in name_lower or "পাট" in name_lower:
            crop = "jute"
        elif "poultry" in name_lower or "মুরগি" in name_lower:
            crop = "poultry"
        elif "fishery" in name_lower or "মাছ" in name_lower or "fish" in name_lower:
            crop = "fishery"

        if "blast" in name_lower or "ব্লাস্ট" in name_lower:
            disease = "blast"
        elif "brown" in name_lower or "বাদামী" in name_lower:
            disease = "brown_leaf_spot"
        elif "curl" in name_lower or "কোকড়ানো" in name_lower:
            disease = "leaf_curl"
        elif "rot" in name_lower or "পচা" in name_lower:
            disease = "stem_rot"

        chunks = []
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to snap to the end of a sentence
            if end < len(text):
                last_period = max(chunk_text.rfind('.'), chunk_text.rfind('।'), chunk_text.rfind('\n'))
                if last_period > chunk_size // 2:
                    end = start + last_period + 1
                    chunk_text = text[start:end]
            
            doc_id = f"{source_name}_chunk_{chunk_idx}"
            metadata = {
                "source_name": source_name,
                "crop": crop,
                "disease": disease,
                "document_type": doc_type,
                "language": "bn" if any(ord(c) > 127 for c in chunk_text) else "en",
                "page_number": page_number,
                "chunk_id": doc_id
            }
            
            chunks.append(RAGDocument(
                id=doc_id,
                text=chunk_text,
                metadata=metadata
            ))
            
            start += (len(chunk_text) - chunk_overlap) if len(chunk_text) > chunk_overlap else len(chunk_text)
            chunk_idx += 1
            
            # Infinite loop safety
            if len(chunk_text) == 0 or start >= len(text):
                break
                
        return chunks
