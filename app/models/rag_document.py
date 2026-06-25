# app/models/rag_document.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class RAGDocument:
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0

    @property
    def source_name(self) -> str:
        return self.metadata.get("source_name", "Unknown Source")

    @property
    def crop(self) -> str:
        return self.metadata.get("crop", "general")

    @property
    def disease(self) -> str:
        return self.metadata.get("disease", "general")

    @property
    def document_type(self) -> str:
        return self.metadata.get("document_type", "manual")

    @property
    def language(self) -> str:
        return self.metadata.get("language", "bn")

    @property
    def page_number(self) -> Optional[int]:
        page = self.metadata.get("page_number")
        if page is not None:
            try:
                return int(page)
            except (ValueError, TypeError):
                pass
        return None

    @property
    def chunk_id(self) -> str:
        return self.metadata.get("chunk_id", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "source_name": self.source_name,
            "page_number": self.page_number,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata
        }
