from pymongo import MongoClient
from datetime import datetime

class ChatHistoryManager:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="Nquiry", collection_name="Users"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def add_message(self, user_id, role, message):
        """Add a message to the user's chat history."""
        self.collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": {
                "role": role,
                "message": message,
                "timestamp": datetime.utcnow()
            }}},
            upsert=True
        )

    def get_history(self, user_id):
        """Retrieve the full chat history for a user."""
        doc = self.collection.find_one({"user_id": user_id})
        return doc["messages"] if doc and "messages" in doc else []

    def clear_history(self, user_id):
        """Clear chat history for a user."""
        self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"messages": []}}
        )

# Example usage:
# chat_mgr = ChatHistoryManager()
# chat_mgr.add_message("user123", "user", "Hello!")
# chat_mgr.add_message("user123", "assistant", "Hi, how can I help?")
# print(chat_mgr.get_history("user123"))
