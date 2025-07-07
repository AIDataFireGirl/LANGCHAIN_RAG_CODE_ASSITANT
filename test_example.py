#!/usr/bin/env python3
"""
Test example for RAG Code Assistant
Demonstrates basic functionality
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

def create_test_files():
    """Create some test files to demonstrate the system"""
    
    # Create test directory
    test_dir = Path("test_codebase")
    test_dir.mkdir(exist_ok=True)
    
    # Create a simple Python file
    python_file = test_dir / "main.py"
    python_file.write_text('''
"""
Example Python application
"""

import os
import json
from typing import Dict, List

class UserManager:
    """Manages user operations"""
    
    def __init__(self):
        self.users = {}
    
    def add_user(self, username: str, email: str) -> bool:
        """Add a new user"""
        if username in self.users:
            return False
        
        self.users[username] = {
            'email': email,
            'created_at': '2024-01-01'
        }
        return True
    
    def get_user(self, username: str) -> Dict:
        """Get user information"""
        return self.users.get(username, {})
    
    def list_users(self) -> List[str]:
        """List all usernames"""
        return list(self.users.keys())

def main():
    """Main application function"""
    manager = UserManager()
    
    # Add some users
    manager.add_user("alice", "alice@example.com")
    manager.add_user("bob", "bob@example.com")
    
    print("Users:", manager.list_users())
    print("Alice's info:", manager.get_user("alice"))

if __name__ == "__main__":
    main()
''')
    
    # Create a configuration file
    config_file = test_dir / "config.py"
    config_file.write_text('''
"""
Configuration settings
"""

# Database configuration
DATABASE_URL = "postgresql://localhost/mydb"
DATABASE_POOL_SIZE = 10

# API configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_DEBUG = True

# Security settings
SECRET_KEY = "your-secret-key-here"
JWT_EXPIRY = 3600

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "app.log"
''')
    
    # Create a utility file
    utils_file = test_dir / "utils.py"
    utils_file.write_text('''
"""
Utility functions
"""

import hashlib
import json
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def save_to_json(data: dict, filename: str) -> bool:
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False
''')
    
    print(f"✅ Created test files in {test_dir}")
    return str(test_dir)

def test_embedding():
    """Test the embedding functionality"""
    try:
        from src.config import config
        from src.embeddings.embedding_manager import embedding_manager
        
        # Create test files
        test_dir = create_test_files()
        
        print("🔍 Testing codebase embedding...")
        
        # Embed the test codebase
        success = embedding_manager.embed_codebase(test_dir)
        
        if success:
            stats = embedding_manager.get_collection_stats()
            print(f"✅ Successfully embedded {stats.get('total_documents', 0)} documents")
            return True
        else:
            print("❌ Failed to embed codebase")
            return False
            
    except Exception as e:
        print(f"❌ Error during embedding test: {str(e)}")
        return False

def test_query():
    """Test query functionality"""
    try:
        from src.assistant.code_assistant import code_assistant
        
        print("💬 Testing query functionality...")
        
        # Test questions
        test_questions = [
            "What is the main function in this codebase?",
            "How is user management implemented?",
            "What are the configuration settings?",
            "Show me the utility functions"
        ]
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            response = code_assistant.ask_question(question)
            
            if response.get('error'):
                print(f"❌ Error: {response['error']}")
            else:
                print(f"🤖 Answer: {response['answer'][:200]}...")
                
                if response.get('sources'):
                    print(f"📚 Sources: {len(response['sources'])} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during query test: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing RAG Code Assistant...")
    
    # Test embedding
    if test_embedding():
        print("✅ Embedding test passed")
        
        # Test queries
        if test_query():
            print("✅ Query test passed")
        else:
            print("❌ Query test failed")
    else:
        print("❌ Embedding test failed")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main() 