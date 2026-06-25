import logging
import chromadb
from chromadb.utils import embedding_functions
from app.config.settings import Config

logger = logging.getLogger(__name__)

class VectorStoreRepository:
    def __init__(self):
        Config.init_app()
        # Persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=str(Config.CHROMA_DB_DIR))
        self.collection_name = "krishi_knowledge"
        
        # Configure embedding function
        # We will try to use Gemini API for embeddings, otherwise fallback to default Chroma embedding function
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

    def add_documents(self, texts, metadatas, ids):
        """
        Add text documents to the vector store.
        """
        if not texts:
            return
        
        # Filter out empty texts
        valid_indices = [i for i, text in enumerate(texts) if text and text.strip()]
        if not valid_indices:
            return
            
        texts = [texts[i] for i in valid_indices]
        metadatas = [metadatas[i] for i in valid_indices]
        ids = [ids[i] for i in valid_indices]
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(texts)} documents to vector store.")

    def search_similar(self, query_text, n_results=3):
        """
        Search for documents similar to the query.
        """
        if not query_text or not query_text.strip():
            return []
            
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
            logger.error(f"Error querying vector store: {e}")
            return []

    def count(self):
        return self.collection.count()

    def reset(self):
        """
        Clear all documents in the collection
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn
            )
            logger.info("Vector store collection reset.")
        except Exception as e:
            logger.error(f"Error resetting vector store: {e}")
