import logging
from app.config.settings import Config

logger = logging.getLogger(__name__)

# Try to import chromadb, fallback gracefully on Vercel or systems without it
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    embedding_functions = None
    logger.warning("chromadb library is not installed. Will use local keyword-ranking fallback.")

class VectorStoreRepository:
    def __init__(self):
        Config.init_app()
        self.collection_name = "krishi_knowledge"
        self.client = None
        self.collection = None
        self.embedding_fn = None
        
        # In-memory seeds for fallback/offline RAG (used on Vercel)
        self.fallback_seeds = [
            {
                "id": "seed_0",
                "text": "Bangladesh Rice Research Institute (BRRI) Blast Control Manual: Rice blast is caused by Magnaporthe oryzae. Symptoms include spindle-shaped leaf lesions and neck rot where panicles collapse. High relative humidity above 85% and warm temperatures of 25-30°C are extremely favorable. Treatment: Suspend Nitrogen/Urea applications. Keep fields irrigated. Apply Tricyclazole 72 WP (Trooper) at 0.75g per liter of water, or Nativo 75 WG at 0.6g per liter of water. Spray in the afternoon.",
                "metadata": {
                    "source_name": "brri_blast_management_guide.txt",
                    "crop": "rice",
                    "disease": "blast",
                    "document_type": "seed",
                    "language": "en",
                    "page_number": 1,
                    "chunk_id": "seed_0"
                }
            },
            {
                "id": "seed_1",
                "text": "BRRI Leaf Spot advisory: Brown Leaf Spot (Bipolaris oryzae) manifests as small oval dark brown lesions on rice foliage. Often associated with potassium-deficient, sandy or low-fertility soils. Control: Apply balanced fertilizers (potash and gypsum). Apply Propiconazole (Tilt 250 EC) at 1ml per liter of water, or Tricyclazole at 0.75g per liter. Spray twice with a 10-12 day gap.",
                "metadata": {
                    "source_name": "brri_brown_spot_guide.txt",
                    "crop": "rice",
                    "disease": "brown_leaf_spot",
                    "document_type": "seed",
                    "language": "en",
                    "page_number": 1,
                    "chunk_id": "seed_1"
                }
            },
            {
                "id": "seed_2",
                "text": "Bangladesh Agricultural Research Institute (BARI) Tomato Management: Leaf curl virus is spread by Whitefly (Bemisia tabaci). Symptoms are downward curling, severe puckering, yellowing and stunted plant height. Viral infections are incurable, so infected plants must be uprooted and buried. Spray systemic vector insecticides: Imidacloprid (Admire or Tido) at 0.5ml per liter, or Acetamiprid (Tundra) at 1g per liter, to eliminate whitefly vectors.",
                "metadata": {
                    "source_name": "bari_tomato_guide.txt",
                    "crop": "tomato",
                    "disease": "leaf_curl",
                    "document_type": "seed",
                    "language": "en",
                    "page_number": 1,
                    "chunk_id": "seed_2"
                }
            },
            {
                "id": "seed_3",
                "text": "Bangladesh Jute Research Institute (BJRI) Stem Rot prevention: Jute stem rot is caused by Macrophomina phaseolina. Dark brown or black lesions occur near the base of the stems, leading to fiber rotting and dry plants. Favorable under waterlogging conditions. Action: Provide drainage. Apply Carbendazim (Autostin or Noin) at 2g per liter of water, or Mancozeb+Metalaxyl (Ridomil Gold) at 2g per liter at the root base. Repeat after 10 days.",
                "metadata": {
                    "source_name": "bjri_jute_disease_manual.txt",
                    "crop": "jute",
                    "disease": "stem_rot",
                    "document_type": "seed",
                    "language": "en",
                    "page_number": 1,
                    "chunk_id": "seed_3"
                }
            }
        ]

        if CHROMADB_AVAILABLE and not Config.VERCEL_DEPLOYMENT:
            try:
                # Persistent ChromaDB client
                self.client = chromadb.PersistentClient(path=str(Config.CHROMA_DB_DIR))
                
                # Configure embedding function
                if Config.GEMINI_API_KEY:
                    try:
                        self.embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                            api_key=Config.GEMINI_API_KEY,
                            model_name="models/embedding-001"
                        )
                        logger.info("ChromaDB initialized with Gemini API embeddings.")
                    except Exception as e:
                        logger.warning(f"Failed to initialize Gemini embeddings: {e}. Falling back to default embedding function.")
                        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
                else:
                    logger.warning(f"No GEMINI_API_KEY provided. Using embedding model: {Config.EMBEDDING_MODEL_NAME}")
                    try:
                        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                            model_name=Config.EMBEDDING_MODEL_NAME
                        )
                    except Exception as e:
                        logger.warning(f"Failed to load sentence-transformers library or model: {e}. Falling back to default Chroma embedding function.")
                        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
                    
                # Get or create collection
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn
                )
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {e}. Reverting to local fallback mode.")
                self.client = None
                self.collection = None
        else:
            logger.info("ChromaDB is unavailable or running on Vercel deployment. Operating in local fallback mode.")

    def add_documents(self, texts, metadatas, ids):
        """
        Add text documents to the vector store.
        """
        if not texts:
            return
            
        if self.collection is None:
            logger.warning("Vector store is operating in read-only fallback mode. Skipping document insertion.")
            return
        
        # Filter out empty texts
        valid_indices = [i for i, text in enumerate(texts) if text and text.strip()]
        if not valid_indices:
            return
            
        texts = [texts[i] for i in valid_indices]
        metadatas = [metadatas[i] for i in valid_indices]
        ids = [ids[i] for i in valid_indices]
        
        try:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(texts)} documents to vector store.")
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}")

    def search_similar(self, query_text, n_results=3):
        """
        Search for documents similar to the query.
        """
        if not query_text or not query_text.strip():
            return []
            
        # If ChromaDB collection is available, use it
        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=n_results
                )
                
                # Format results
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                ids = results.get("ids", [[]])[0]
                
                formatted_results = []
                for i in range(len(documents)):
                    formatted_results.append({
                        "id": ids[i],
                        "text": documents[i],
                        "metadata": metadatas[i],
                        "distance": distances[i] if i < len(distances) else 0.0
                    })
                return formatted_results
            except Exception as e:
                logger.error(f"Error querying ChromaDB collection: {e}. Falling back to keyword search.")

        # Local Keyword-ranking fallback (extremely useful for Vercel/mock modes)
        query_words = set(query_text.lower().replace("|", " ").replace(",", " ").split())
        scored_seeds = []
        
        for seed in self.fallback_seeds:
            score = 0
            text_lower = seed["text"].lower()
            crop_lower = seed["metadata"]["crop"].lower()
            disease_lower = seed["metadata"]["disease"].lower()
            
            for word in query_words:
                if len(word) > 2:
                    if word in text_lower:
                        score += 1
                    if word in crop_lower:
                        score += 8  # Heavy weight for crop match
                    if word in disease_lower:
                        score += 8  # Heavy weight for disease match
            
            # Distance mapping (lower is better, max distance 2.0)
            # A score of 0 gives 1.5 distance. High scores get close to 0.1
            distance = max(0.1, min(1.9, 1.5 - (score / 15.0)))
            scored_seeds.append((score, distance, seed))
            
        # Sort by score descending (highest keyword matches first)
        scored_seeds.sort(key=lambda x: x[0], reverse=True)
        
        # Format results
        formatted_results = []
        for score, dist, seed in scored_seeds[:n_results]:
            # On Vercel, label the source name internally as 'static_demo_rag'
            meta = seed["metadata"].copy()
            if Config.VERCEL_DEPLOYMENT:
                meta["source_name"] = "static_demo_rag"
                
            formatted_results.append({
                "id": seed["id"],
                "text": seed["text"],
                "metadata": meta,
                "distance": dist
            })
            
        logger.info(f"Local RAG fallback search completed. Found {len(formatted_results)} results.")
        return formatted_results

    def count(self):
        if self.collection is not None:
            try:
                return self.collection.count()
            except Exception:
                pass
        return len(self.fallback_seeds)

    def reset(self):
        """
        Clear all documents in the collection
        """
        if self.collection is None:
            logger.warning("Vector store is in fallback mode. Reset ignored.")
            return
            
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn
            )
            logger.info("Vector store collection reset.")
        except Exception as e:
            logger.error(f"Error resetting vector store: {e}")
