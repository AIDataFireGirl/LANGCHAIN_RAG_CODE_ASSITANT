"""
Pydantic models for API requests and responses
Provides data validation and serialization
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class EmbedCodebaseRequest(BaseModel):
    """Request model for embedding codebase"""
    directory_path: str = Field(..., description="Path to directory containing code files")
    recursive: bool = Field(default=True, description="Whether to scan subdirectories")

class EmbedCodebaseResponse(BaseModel):
    """Response model for embedding codebase"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    files_processed: int = Field(default=0, description="Number of files processed")
    documents_created: int = Field(default=0, description="Number of documents created")

class AskQuestionRequest(BaseModel):
    """Request model for asking questions"""
    question: str = Field(..., description="Question about the codebase", min_length=1, max_length=1000)

class SourceDocument(BaseModel):
    """Model for source document information"""
    content: str = Field(..., description="Document content preview")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")

class AskQuestionResponse(BaseModel):
    """Response model for asking questions"""
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceDocument] = Field(default=[], description="Source documents used")
    error: Optional[str] = Field(default=None, description="Error message if any")

class SystemInfoResponse(BaseModel):
    """Response model for system information"""
    model_name: str = Field(..., description="LLM model name")
    temperature: float = Field(..., description="Model temperature")
    max_tokens: int = Field(..., description="Maximum tokens")
    vector_store_stats: Dict[str, Any] = Field(..., description="Vector store statistics")
    conversation_history_length: int = Field(..., description="Number of conversation turns")

class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history"""
    messages: List[Dict[str, str]] = Field(..., description="List of conversation messages")

class ClearHistoryResponse(BaseModel):
    """Response model for clearing history"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    openai_configured: bool = Field(..., description="Whether OpenAI is configured")
    vector_store_ready: bool = Field(..., description="Whether vector store is ready") 