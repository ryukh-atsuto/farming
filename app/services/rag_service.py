# app/services/rag_service.py
import logging
from pathlib import Path
from typing import List, Dict, Any
from app.repositories.vector_store import VectorStoreRepository
from app.repositories.document_store import DocumentStore
from app.models.rag_document import RAGDocument

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, vector_store: VectorStoreRepository = None, doc_store: DocumentStore = None):
        self.vector_store = vector_store or VectorStoreRepository()
        self.doc_store = doc_store or DocumentStore()
        
        # Auto-seed default guides on init if ChromaDB collection is empty
        try:
            if self.vector_store.count() == 0:
                logger.info("ChromaDB is empty. Running auto-seeding...")
                self.seed_from_defaults()
        except Exception as e:
            logger.error(f"Error checking vector store state during initialization: {e}")

    def query_knowledge(self, query_text: str, crop: str = None, symptoms: List[str] = None, english_translation: str = None, n_results: int = 3) -> Dict[str, Any]:
        """
        Retrieves top relevant RAG chunks by constructing a rich search prompt.
        Prioritizes matches matching the crop name.
        """
        # Build search query
        search_terms = []
        if crop and crop.lower() != "unknown":
            search_terms.append(crop)
        if symptoms:
            search_terms.extend(symptoms)
        if english_translation:
            search_terms.append(english_translation)
        search_terms.append(query_text)
        
        search_query = " | ".join(search_terms)
        logger.info(f"Querying knowledge RAG: '{search_query}' (crop: '{crop}')")
        
        results = self.vector_store.search_similar(search_query, n_results=n_results)
        
        retrieved_chunks = []
        for res in results:
            # Format as RAGDocument
            metadata = res.get("metadata", {})
            distance = res.get("distance", 1.0)
            
            # Simple conversion from distance to score (chromadb cosine distance is between 0 and 2, 0 is best)
            # Normalise to [0, 1] range where 1.0 is highest match
            relevance_score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
            
            retrieved_chunks.append({
                "source_name": metadata.get("source_name", "Unknown Source"),
                "page_number": metadata.get("page_number", 1),
                "text": res.get("text", ""),
                "relevance_score": round(relevance_score, 2),
                "crop": metadata.get("crop", "general"),
                "disease": metadata.get("disease", "general")
            })

        # Priority filter: Sort chunks matching the crop to the top
        if crop and crop.lower() != "unknown":
            matching_crop = []
            other_crops = []
            for chunk in retrieved_chunks:
                if chunk["crop"].lower() == crop.lower():
                    matching_crop.append(chunk)
                else:
                    other_crops.append(chunk)
            retrieved_chunks = matching_crop + other_crops

        return {"retrieved_chunks": retrieved_chunks}

    def ingest_directory_documents(self) -> int:
        """Loads and indexes all documents from knowledge_base directory."""
        logger.info("Ingesting documents from knowledge base directory...")
        documents = self.doc_store.load_documents()
        if not documents:
            logger.info("No documents found in knowledge base folder.")
            return 0

        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [doc.id for doc in documents]

        self.vector_store.add_documents(texts, metadatas, ids)
        logger.info(f"Ingested {len(documents)} chunks to vector store.")
        return len(documents)

    def seed_from_defaults(self):
        """Seeds default agricultural guidelines for the main demo crops."""
        seeds = [
            {
                "crop": "rice",
                "disease": "blast",
                "source_name": "brri_blast_management_guide.txt",
                "text": "Bangladesh Rice Research Institute (BRRI) Blast Control Manual: Rice blast is caused by Magnaporthe oryzae. Symptoms include spindle-shaped leaf lesions and neck rot where panicles collapse. High relative humidity above 85% and warm temperatures of 25-30°C are extremely favorable. Treatment: Suspend Nitrogen/Urea applications. Keep fields irrigated. Apply Tricyclazole 72 WP (Trooper) at 0.75g per liter of water, or Nativo 75 WG at 0.6g per liter of water. Spray in the afternoon."
            },
            {
                "crop": "rice",
                "disease": "brown_leaf_spot",
                "source_name": "brri_brown_spot_guide.txt",
                "text": "BRRI Leaf Spot advisory: Brown Leaf Spot (Bipolaris oryzae) manifests as small oval dark brown lesions on rice foliage. Often associated with potassium-deficient, sandy or low-fertility soils. Control: Apply balanced fertilizers (potash and gypsum). Apply Propiconazole (Tilt 250 EC) at 1ml per liter of water, or Tricyclazole at 0.75g per liter. Spray twice with a 10-12 day gap."
            },
            {
                "crop": "tomato",
                "disease": "leaf_curl",
                "source_name": "bari_tomato_guide.txt",
                "text": "Bangladesh Agricultural Research Institute (BARI) Tomato Management: Leaf curl virus is spread by Whitefly (Bemisia tabaci). Symptoms are downward curling, severe puckering, yellowing and stunted plant height. Viral infections are incurable, so infected plants must be uprooted and buried. Spray systemic vector insecticides: Imidacloprid (Admire or Tido) at 0.5ml per liter, or Acetamiprid (Tundra) at 1g per liter, to eliminate whitefly vectors."
            },
            {
                "crop": "jute",
                "disease": "stem_rot",
                "source_name": "bjri_jute_disease_manual.txt",
                "text": "Bangladesh Jute Research Institute (BJRI) Stem Rot prevention: Jute stem rot is caused by Macrophomina phaseolina. Dark brown or black lesions occur near the base of the stems, leading to fiber rotting and dry plants. Favorable under waterlogging conditions. Action: Provide drainage. Apply Carbendazim (Autostin or Noin) at 2g per liter of water, or Mancozeb+Metalaxyl (Ridomil Gold) at 2g per liter at the root base. Repeat after 10 days."
            }
        ]

        texts = [s["text"] for s in seeds]
        metadatas = [{
            "source_name": s["source_name"],
            "crop": s["crop"],
            "disease": s["disease"],
            "document_type": "seed",
            "language": "en",
            "page_number": 1,
            "chunk_id": f"seed_{idx}"
        } for idx, s in enumerate(seeds)]
        ids = [f"seed_{idx}" for idx in range(len(seeds))]

        self.vector_store.add_documents(texts, metadatas, ids)
        logger.info("Successfully seeded database with default crop guidelines.")
