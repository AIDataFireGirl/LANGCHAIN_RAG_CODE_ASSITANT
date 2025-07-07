"""
Code Assistant for RAG Code Assistant
Combines retrieval and generation using LangChain
"""

import logging
from typing import List, Dict, Optional, Any
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from src.config import config
from src.embeddings.embedding_manager import embedding_manager

# Configure logging
logger = logging.getLogger(__name__)

class CodeAssistant:
    """Main code assistant that handles queries and provides responses"""
    
    def __init__(self):
        """Initialize the code assistant with LLM and retrieval chain"""
        try:
            # Initialize OpenAI chat model
            self.llm = ChatOpenAI(
                openai_api_key=config.OPENAI.API_KEY,
                model_name=config.OPENAI.MODEL_NAME,
                temperature=config.OPENAI.TEMPERATURE,
                max_tokens=config.OPENAI.MAX_TOKENS
            )
            
            # Initialize conversation memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create custom prompt template for code assistance
            self.prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""
You are a helpful code assistant that helps developers understand and work with their codebase.

Context from the codebase:
{context}

Question: {question}

Please provide a helpful and accurate response based on the code context. If the context doesn't contain enough information to answer the question, say so. Always be specific and reference the code when possible.

Answer:"""
            )
            
            # Initialize retrieval chain
            self.retrieval_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=embedding_manager.vector_store.as_retriever(
                    search_kwargs={"k": 5}
                ),
                memory=self.memory,
                return_source_documents=True,
                verbose=config.DEBUG
            )
            
            logger.info("Code assistant initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing code assistant: {str(e)}")
            raise
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Ask a question about the codebase
        
        Args:
            question: The question to ask
            
        Returns:
            Dict[str, Any]: Response with answer and source documents
        """
        try:
            # Validate input
            if not question or not question.strip():
                return {
                    'answer': 'Please provide a valid question.',
                    'sources': [],
                    'error': None
                }
            
            # Check if vector store has documents
            stats = embedding_manager.get_collection_stats()
            if stats.get('total_documents', 0) == 0:
                return {
                    'answer': 'No codebase has been embedded yet. Please embed your codebase first.',
                    'sources': [],
                    'error': None
                }
            
            # Get response from retrieval chain
            response = self.retrieval_chain({"question": question})
            
            # Extract answer and sources
            answer = response.get('answer', 'No answer generated.')
            source_documents = response.get('source_documents', [])
            
            # Format source documents
            sources = []
            for doc in source_documents:
                sources.append({
                    'content': doc.page_content[:500] + '...' if len(doc.page_content) > 500 else doc.page_content,
                    'metadata': doc.metadata
                })
            
            logger.info(f"Generated answer for question: {question[:100]}...")
            
            return {
                'answer': answer,
                'sources': sources,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                'answer': 'Sorry, I encountered an error while processing your question.',
                'sources': [],
                'error': str(e)
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history
        
        Returns:
            List[Dict[str, str]]: List of conversation turns
        """
        try:
            return self.memory.chat_memory.messages
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    def clear_conversation_history(self) -> bool:
        """
        Clear conversation history
        
        Returns:
            bool: True if successful
        """
        try:
            self.memory.clear()
            logger.info("Cleared conversation history")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information and statistics
        
        Returns:
            Dict[str, Any]: System information
        """
        try:
            stats = embedding_manager.get_collection_stats()
            
            return {
                'model_name': config.OPENAI.MODEL_NAME,
                'temperature': config.OPENAI.TEMPERATURE,
                'max_tokens': config.OPENAI.MAX_TOKENS,
                'vector_store_stats': stats,
                'conversation_history_length': len(self.get_conversation_history())
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {}

# Global code assistant instance
code_assistant = CodeAssistant() 