import sqlite3
import secrets
import hashlib

from typing import List

# Dataset Setup
def init_db():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor() 

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Create conversations table
    cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT NOT NULL,
    summary TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")
    
    # Create messages Table 
    cursor.execute("""
CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,   
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
)
""")

    conn.commit()
    conn.close()

def hash_password(password: str, salt: str=None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)

    return salt, pwdhash.hex()

def verify_password(stored_pwd: str, stored_salt: str, provided_pwd: str) -> bool:
    _, pwdhash = hash_password(provided_pwd, stored_salt)
    return pwdhash == stored_pwd

def create_user(username: str, password: str) -> bool:
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    
    try:

        # Hash the password to a new salt
        salt, pwdhash = hash_password(password)

        # Insert the new user
        c.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", 
                  (username, pwdhash, salt))
       
        conn.commit()
        return True
    
    except sqlite3.IntegrityError:
        return False
    
    finally:
        conn.close()


def authenticate_user(username: str, password:str)->tuple:
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("SELECT id, password_hash, salt FROM users WHERE username =?", 
    (username,))
    result = c.fetchone()
    conn.close()
    if result is None:
        return False, None
    user_id, stored_hash, salt = result
    if verify_password(stored_hash, salt, password):
        return True, user_id
    else:
       return False, None

def store_message(session_id: str, role: str, content: str, model_used: str, user_id: int)-> None:
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    # Get current conversation id or create new one 
    cursor.execute("SELECT id FROM conversations WHERE session_id = ? AND user_id=? ORDER BY timestamp DESC LIMIT 1", (session_id, user_id))
    result = cursor.fetchone()

    if result is None:
        cursor.execute("INSERT INTO conversations (session_id, user_id, model_used) VALUES (?, ?, ?)", (session_id, user_id, model_used))
        conversation_id = cursor.lastrowid
    else:
        conversation_id = result[0]

    # Store message 
    cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conversation_id, role, content))

    conn.commit()
    conn.close()

def get_recent_conversations(session_id:str, user_id:int, limit:int=5, model_filter:str=None)->List:
    conn = sqlite3.connect("chatbot.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get recent conversation's ID
    if model_filter:
        cursor.execute("""
SELECT id, timestamp, model_used FROM conversations
    WHERE session_id = ? AND user_id = ? AND model_used = ?
    ORDER BY timestamp DESC
    LIMIT ?
""", (session_id, user_id, model_filter, limit))
    else:
        cursor.execute("""
SELECT id, timestamp, model_used FROM conversations 
WHERE session_id = ? AND user_id = ?
ORDER BY timestamp DESC
LIMIT ?
""", (session_id, user_id, limit))
    
    conversations = []

    for conv_row in cursor.fetchall():
        conv_id = conv_row["id"]

        # Get messages for this conversations
        cursor.execute("""
SELECT role, content FROM messages 
WHERE conversation_id = ? 
ORDER BY timestamp ASC
""", (conv_id,))
        
        messages = []
        for msg in cursor.fetchall():
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        conversations.append({
            "id": conv_id,
            "timestamp": conv_row["timestamp"],
            "model_used": conv_row["model_used"],
            "messages": messages
        })

    conn.close()
    return conversations 

def store_conversation_summary(session_id:str, user_id:int, conv_id:int, summary:str)->None:
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM conversations WHERE session_id = ? AND user_id = ?", 
    (conv_id, user_id))

    if cursor.fetchone() is not None:
        cursor.execute("UPDATE conversations SET summary = ? WHERE id = ?", 
    (summary, conv_id))
        conn.commit()
    
    conn.close()

if __name__ == "__main__":
    print(globals())