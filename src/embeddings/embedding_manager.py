"""
Embedding manager for RAG Code Assistant
Handles vector embeddings using LangChain and ChromaDB
"""

import logging
from typing import List, Dict, Optional, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from src.config import config
from src.utils.file_processor import file_processor

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manages code embeddings and vector storage"""
    
    def __init__(self):
        """Initialize embedding manager with OpenAI embeddings and ChromaDB"""
        try:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=config.OPENAI.API_KEY,
                model="text-embedding-ada-002"
            )
            
            # Initialize text splitter for chunking
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Initialize vector store
            self.vector_store = Chroma(
                persist_directory=config.DATABASE.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=config.DATABASE.COLLECTION_NAME
            )
            
            logger.info("Embedding manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing embedding manager: {str(e)}")
            raise
    
    def create_documents_from_files(self, file_paths: List[str]) -> List[Document]:
        """
        Create LangChain documents from file paths
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List[Document]: List of LangChain documents
        """
        documents = []
        
        for file_path in file_paths:
            try:
                # Read file content
                content = file_processor.read_file_content(file_path)
                if not content:
                    continue
                
                # Get file metadata
                metadata = file_processor.get_file_metadata(file_path)
                
                # Create document
                document = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(document)
                
                logger.info(f"Created document for: {file_path}")
                
            except Exception as e:
                logger.error(f"Error creating document for {file_path}: {str(e)}")
                continue
        
        logger.info(f"Created {len(documents)} documents from {len(file_paths)} files")
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for better retrieval
        
        Args:
            documents: List of documents to split
            
        Returns:
            List[Document]: List of split documents
        """
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
            return split_docs
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            return documents
    
    def add_documents_to_vectorstore(self, documents: List[Document]) -> bool:
        """
        Add documents to vector store
        
        Args:
            documents: List of documents to add
            
        Returns:
            bool: True if successful
        """
        try:
            if not documents:
                logger.warning("No documents to add to vector store")
                return False
            
            # Split documents if they're too large
            split_docs = self.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(split_docs)
            
            # Persist to disk
            self.vector_store.persist()
            
            logger.info(f"Successfully added {len(split_docs)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            return False
    
    def embed_codebase(self, directory_path: str) -> bool:
        """
        Embed entire codebase from directory
        
        Args:
            directory_path: Path to directory containing code files
            
        Returns:
            bool: True if successful
        """
        try:
            # Scan directory for valid files
            file_paths = file_processor.scan_directory(directory_path)
            
            if not file_paths:
                logger.warning(f"No valid files found in {directory_path}")
                return False
            
            # Create documents from files
            documents = self.create_documents_from_files(file_paths)
            
            if not documents:
                logger.warning("No documents created from files")
                return False
            
            # Add to vector store
            success = self.add_documents_to_vectorstore(documents)
            
            if success:
                logger.info(f"Successfully embedded codebase from {directory_path}")
            else:
                logger.error(f"Failed to embed codebase from {directory_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error embedding codebase: {str(e)}")
            return False
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar code snippets
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with scores
        """
        try:
            # Search vector store
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': float(score)
                })
            
            logger.info(f"Found {len(formatted_results)} similar documents for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection
        
        Returns:
            Dict[str, Any]: Collection statistics
        """
        try:
            collection = self.vector_store._collection
            count = collection.count()
            
            return {
                'total_documents': count,
                'collection_name': config.DATABASE.COLLECTION_NAME,
                'persist_directory': config.DATABASE.CHROMA_PERSIST_DIRECTORY
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def clear_vectorstore(self) -> bool:
        """
        Clear all documents from vector store
        
        Returns:
            bool: True if successful
        """
        try:
            self.vector_store._collection.delete(where={})
            logger.info("Cleared vector store")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            return False

# Global embedding manager instance
embedding_manager = EmbeddingManager() 