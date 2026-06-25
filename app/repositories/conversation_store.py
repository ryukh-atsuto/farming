import json
import logging
from pathlib import Path
from app.config.settings import Config
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)

class ConversationStoreRepository:
    def __init__(self):
        Config.init_app()
        self.filepath = Path(Config.CONVERSATION_HISTORY_FILE)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.filepath.exists():
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
                logger.info(f"Initialized conversation database at {self.filepath}")
            except Exception as e:
                logger.error(f"Error creating conversation file: {e}")

    def _read_all(self):
        self._ensure_file_exists()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data_list = json.load(f)
                if not isinstance(data_list, list):
                    return []
                return data_list
        except Exception as e:
            logger.error(f"Error reading conversation database: {e}")
            return []

    def _write_all(self, data_list):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error writing to conversation database: {e}")

    def save_conversation(self, conversation: Conversation):
        """
        Save or update a conversation.
        """
        conv_dict = conversation.to_dict()
        conversations = self._read_all()
        
        # Check if conversation already exists, update it if so
        exists = False
        for idx, item in enumerate(conversations):
            if item.get("conversation_id") == conversation.conversation_id:
                conversations[idx] = conv_dict
                exists = True
                break
                
        if not exists:
            conversations.append(conv_dict)
            
        # Sort by timestamp descending
        try:
            conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        except Exception:
            pass
            
        self._write_all(conversations)
        logger.info(f"Saved conversation {conversation.conversation_id}")

    def get_conversation(self, conversation_id: str) -> Conversation:
        """
        Retrieve a single conversation by ID.
        """
        conversations = self._read_all()
        for item in conversations:
            if item.get("conversation_id") == conversation_id:
                return Conversation.from_dict(item)
        return None

    def get_history(self, limit: int = 15) -> list:
        """
        Retrieve recent conversations.
        """
        conversations = self._read_all()
        # Parse into objects
        parsed_list = [Conversation.from_dict(item) for item in conversations]
        return parsed_list[:limit]

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from history.
        """
        conversations = self._read_all()
        filtered = [item for item in conversations if item.get("conversation_id") != conversation_id]
        success = False
        if len(filtered) < len(conversations):
            self._write_all(filtered)
            logger.info(f"Deleted conversation {conversation_id}")
            success = True
            
        detailed_file = Path(Config.DATA_DIR) / "history_detailed.json"
        if detailed_file.exists():
            try:
                with open(detailed_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if conversation_id in data:
                    del data[conversation_id]
                    with open(detailed_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    success = True
            except Exception as e:
                logger.error(f"Error deleting from history_detailed.json: {e}")
                
        return success

    def save_history(self, conversation_id: str, payload: dict):
        """
        Save detailed query session payload.
        """
        import datetime
        if "timestamp" not in payload:
            payload["timestamp"] = datetime.datetime.utcnow().isoformat()
        
        detailed_file = Path(Config.DATA_DIR) / "history_detailed.json"
        data = {}
        if detailed_file.exists():
            try:
                with open(detailed_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading history_detailed.json: {e}")
                
        data[conversation_id] = payload
        
        try:
            detailed_file.parent.mkdir(parents=True, exist_ok=True)
            with open(detailed_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved history detailed payload for {conversation_id}")
        except Exception as e:
            logger.error(f"Error writing history_detailed.json: {e}")

    def get_history_by_id(self, conversation_id: str) -> dict:
        """
        Retrieve detailed query session payload by ID.
        """
        detailed_file = Path(Config.DATA_DIR) / "history_detailed.json"
        if not detailed_file.exists():
            return None
        try:
            with open(detailed_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(conversation_id)
        except Exception as e:
            logger.error(f"Error reading history_detailed.json: {e}")
            return None

    def get_all_history(self) -> list:
        """
        Retrieve all detailed query session payloads as a list.
        """
        detailed_file = Path(Config.DATA_DIR) / "history_detailed.json"
        if not detailed_file.exists():
            return []
        try:
            with open(detailed_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return list(data.values())
        except Exception as e:
            logger.error(f"Error reading history_detailed.json: {e}")
            return []

    def clear_all(self):
        """
        Clears all conversation records and detailed history files.
        """
        self._write_all([])
        detailed_file = Path(Config.DATA_DIR) / "history_detailed.json"
        if detailed_file.exists():
            try:
                detailed_file.unlink()
                logger.info("Deleted history_detailed.json")
            except Exception as e:
                logger.error(f"Error deleting history_detailed.json: {e}")

