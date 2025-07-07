"""
Streamlit web interface for RAG Code Assistant
Provides a user-friendly interface for code queries
"""

import streamlit as st
import requests
import json
import os
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = "http://localhost:8000"

def check_api_health() -> bool:
    """Check if the API is running and healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        return False

def embed_codebase(directory_path: str) -> Dict[str, Any]:
    """Embed a codebase directory"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/embed-codebase",
            json={"directory_path": directory_path, "recursive": True},
            timeout=30
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error embedding codebase: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

def ask_question(question: str) -> Dict[str, Any]:
    """Ask a question about the codebase"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json={"question": question},
            timeout=30
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error asking question: {str(e)}")
        return {"answer": f"Error: {str(e)}", "sources": [], "error": str(e)}

def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    try:
        response = requests.get(f"{API_BASE_URL}/system-info", timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {}

def clear_conversation_history() -> bool:
    """Clear conversation history"""
    try:
        response = requests.delete(f"{API_BASE_URL}/conversation-history", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return False

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="RAG Code Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for modern UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🤖 RAG Code Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Your AI-powered code companion")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ API server is not running. Please start the API server first.")
        st.info("To start the API server, run: `python -m uvicorn src.api.routes:app --reload`")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🛠️ Configuration")
        
        # Embed codebase section
        st.markdown("### 📁 Embed Codebase")
        directory_path = st.text_input(
            "Directory Path",
            placeholder="Enter path to your codebase",
            help="Path to the directory containing your code files"
        )
        
        if st.button("🚀 Embed Codebase", type="primary"):
            if directory_path and os.path.exists(directory_path):
                with st.spinner("Embedding codebase..."):
                    result = embed_codebase(directory_path)
                    if result.get("success"):
                        st.success(f"✅ {result['message']}")
                        st.info(f"📊 Files processed: {result.get('files_processed', 0)}")
                    else:
                        st.error(f"❌ {result.get('message', 'Unknown error')}")
            else:
                st.error("Please enter a valid directory path")
        
        st.markdown("---")
        
        # System info
        st.markdown("### 📊 System Info")
        if st.button("🔄 Refresh Info"):
            info = get_system_info()
            if info:
                st.json(info)
        
        # Clear history
        st.markdown("### 🗑️ Clear History")
        if st.button("🗑️ Clear Conversation"):
            if clear_conversation_history():
                st.success("✅ Conversation history cleared")
            else:
                st.error("❌ Failed to clear history")
    
    # Main content
    tab1, tab2 = st.tabs(["💬 Chat", "📋 Instructions"])
    
    with tab1:
        st.markdown('<h2 class="sub-header">💬 Ask Questions About Your Code</h2>', unsafe_allow_html=True)
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your codebase..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    response = ask_question(prompt)
                    
                    if response.get("error"):
                        st.error(f"❌ Error: {response['error']}")
                    else:
                        # Display answer
                        st.markdown(response["answer"])
                        
                        # Display sources if available
                        if response.get("sources"):
                            with st.expander("📚 View Sources"):
                                for i, source in enumerate(response["sources"], 1):
                                    st.markdown(f"**Source {i}:**")
                                    st.code(source["content"], language="text")
                                    st.json(source["metadata"])
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response.get("answer", "Sorry, I couldn't process your question.")
                    })
    
    with tab2:
        st.markdown('<h2 class="sub-header">📋 How to Use</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 🚀 Getting Started
        
        1. **Embed Your Codebase**: Use the sidebar to embed your codebase directory
        2. **Ask Questions**: Use the chat interface to ask questions about your code
        3. **Get Insights**: The AI will provide answers based on your actual code
        
        ### 💡 Example Questions
        
        - "What is the main function in this codebase?"
        - "How is authentication handled?"
        - "Show me all the API endpoints"
        - "What are the database models?"
        - "How is error handling implemented?"
        
        ### 🔧 Supported File Types
        
        The system supports various code file types including:
        - Python (.py)
        - JavaScript (.js, .ts)
        - Java (.java)
        - C/C++ (.c, .cpp, .h)
        - Go (.go)
        - Rust (.rs)
        - And many more...
        
        ### ⚠️ Security Features
        
        - File size limits to prevent memory issues
        - Input validation to prevent harmful queries
        - Secure file processing with validation
        - Rate limiting and error handling
        
        ### 🔍 How It Works
        
        1. **Embedding**: Your code is processed and converted to vector embeddings
        2. **Storage**: Embeddings are stored in a vector database (ChromaDB)
        3. **Retrieval**: When you ask a question, relevant code snippets are retrieved
        4. **Generation**: The AI generates answers based on the retrieved context
        """)

if __name__ == "__main__":
    main() 