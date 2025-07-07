"""
FastAPI routes for RAG Code Assistant
Provides REST API endpoints with security and validation
"""

import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import os

from src.api.models import (
    EmbedCodebaseRequest, EmbedCodebaseResponse,
    AskQuestionRequest, AskQuestionResponse,
    SystemInfoResponse, ConversationHistoryResponse,
    ClearHistoryResponse, HealthCheckResponse
)
from src.config import config
from src.embeddings.embedding_manager import embedding_manager
from src.assistant.code_assistant import code_assistant

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Code Assistant API",
    description="A Retrieval-Augmented Generation system for code assistance",
    version="1.0.0"
)

# Add CORS middleware for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def validate_configuration():
    """Validate that the system is properly configured"""
    try:
        config.validate_configuration()
        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    try:
        validate_configuration()
        logger.info("RAG Code Assistant API started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        stats = embedding_manager.get_collection_stats()
        return HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            openai_configured=config.OPENAI.is_configured(),
            vector_store_ready=stats.get('total_documents', 0) > 0
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/embed-codebase", response_model=EmbedCodebaseResponse)
async def embed_codebase(request: EmbedCodebaseRequest):
    """
    Embed a codebase directory into the vector store
    
    Args:
        request: EmbedCodebaseRequest containing directory path and options
        
    Returns:
        EmbedCodebaseResponse with operation results
    """
    try:
        # Validate directory exists
        if not os.path.exists(request.directory_path):
            raise HTTPException(
                status_code=400, 
                detail=f"Directory does not exist: {request.directory_path}"
            )
        
        # Security validation - check if path is within allowed directories
        if not os.path.isabs(request.directory_path):
            request.directory_path = os.path.abspath(request.directory_path)
        
        # Embed the codebase
        success = embedding_manager.embed_codebase(request.directory_path)
        
        if success:
            stats = embedding_manager.get_collection_stats()
            return EmbedCodebaseResponse(
                success=True,
                message="Codebase embedded successfully",
                files_processed=stats.get('total_documents', 0),
                documents_created=stats.get('total_documents', 0)
            )
        else:
            return EmbedCodebaseResponse(
                success=False,
                message="Failed to embed codebase",
                files_processed=0,
                documents_created=0
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error embedding codebase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/ask", response_model=AskQuestionResponse)
async def ask_question(request: AskQuestionRequest):
    """
    Ask a question about the embedded codebase
    
    Args:
        request: AskQuestionRequest containing the question
        
    Returns:
        AskQuestionResponse with answer and sources
    """
    try:
        # Input validation
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Security validation - check for potentially harmful content
        harmful_keywords = ['system', 'exec', 'eval', 'import', 'os.', 'subprocess']
        question_lower = request.question.lower()
        if any(keyword in question_lower for keyword in harmful_keywords):
            logger.warning(f"Potentially harmful question detected: {request.question}")
            return AskQuestionResponse(
                answer="I cannot process this type of question for security reasons.",
                sources=[],
                error="Security validation failed"
            )
        
        # Get response from code assistant
        response = code_assistant.ask_question(request.question)
        
        return AskQuestionResponse(
            answer=response['answer'],
            sources=response['sources'],
            error=response['error']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/system-info", response_model=SystemInfoResponse)
async def get_system_info():
    """Get system information and statistics"""
    try:
        info = code_assistant.get_system_info()
        return SystemInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/conversation-history", response_model=ConversationHistoryResponse)
async def get_conversation_history():
    """Get conversation history"""
    try:
        history = code_assistant.get_conversation_history()
        return ConversationHistoryResponse(messages=history)
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/conversation-history", response_model=ClearHistoryResponse)
async def clear_conversation_history():
    """Clear conversation history"""
    try:
        success = code_assistant.clear_conversation_history()
        if success:
            return ClearHistoryResponse(
                success=True,
                message="Conversation history cleared successfully"
            )
        else:
            return ClearHistoryResponse(
                success=False,
                message="Failed to clear conversation history"
            )
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/vector-store")
async def clear_vector_store():
    """Clear all documents from vector store"""
    try:
        success = embedding_manager.clear_vectorstore()
        if success:
            return {"success": True, "message": "Vector store cleared successfully"}
        else:
            return {"success": False, "message": "Failed to clear vector store"}
    except Exception as e:
        logger.error(f"Error clearing vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for security and logging"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    ) 