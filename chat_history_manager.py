from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

class ChatHistoryManager:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="Nquiry", collection_name="Users"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def get_ist_time(self):
        """Get current time in IST (Indian Standard Time)"""
        # Get current UTC time and add IST offset (5 hours 30 minutes)
        utc_now = datetime.utcnow()
        ist_offset = timedelta(hours=5, minutes=30)
        ist_time = utc_now + ist_offset
        # Return as naive datetime (without timezone info) so frontend treats it correctly
        return ist_time

    def add_message(self, user_id, role, message, session_id=None, images=None):
        """Add a message to the user's chat history."""
        message_data = {
            "role": role,
            "message": message,
            "timestamp": self.get_ist_time()
        }
        
        # Add session_id if provided (for conversation grouping)
        if session_id:
            message_data["session_id"] = session_id
            
        # Add images if provided (for user messages with uploaded images)
        if images and len(images) > 0:
            # Store essential image data for frontend display
            image_data = []
            for img in images:
                # Handle both dict and ImageData object formats
                if hasattr(img, 'base64'):  # ImageData object
                    image_data.append({
                        "name": img.name,
                        "type": img.type,
                        "base64": img.base64,
                        "preview": img.base64  # Use base64 as preview
                    })
                else:  # Dict format (fallback)
                    image_data.append({
                        "name": img.get("name", "image.png"),
                        "type": img.get("type", "image/png"),
                        "base64": img.get("base64", ""),
                        "preview": img.get("preview", img.get("base64", ""))
                    })
            message_data["images"] = image_data
            print(f"💾 Saving message with {len(image_data)} images")
            
        self.collection.update_one(
            {"user_id": user_id},
            {"$push": {"messages": message_data}},
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

    def delete_conversation_by_question(self, user_id, question):
        """Delete a conversation identified by the exact user question.

        This will remove the user message matching `question` and any
        subsequent assistant messages until the next user message.
        Returns True if any deletion was performed, False otherwise.
        """
        doc = self.collection.find_one({"user_id": user_id})
        if not doc or 'messages' not in doc:
            return False

        messages = doc['messages']
        new_messages = []
        i = 0
        deleted = False

        while i < len(messages):
            msg = messages[i]
            # Match exact user question
            if msg.get('role') == 'user' and str(msg.get('message', '')).strip() == str(question).strip():
                # Skip this user message
                i += 1
                deleted = True

                # Skip following assistant messages until next user message
                while i < len(messages) and messages[i].get('role') == 'assistant':
                    i += 1

                # continue without appending the skipped messages
                continue

            # Otherwise keep the message
            new_messages.append(msg)
            i += 1

        if deleted:
            # Update the document with the filtered messages
            self.collection.update_one({"user_id": user_id}, {"$set": {"messages": new_messages}})

        return deleted

# Example usage:
# chat_mgr = ChatHistoryManager()
# chat_mgr.add_message("user123", "user", "Hello!")
# chat_mgr.add_message("user123", "assistant", "Hi, how can I help?")
# print(chat_mgr.get_history("user123"))
