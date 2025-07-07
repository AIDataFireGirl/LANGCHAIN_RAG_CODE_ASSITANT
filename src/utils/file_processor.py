"""
File processing utilities for RAG Code Assistant
Handles file reading, validation, and chunking with security guard rails
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Generator
import logging
from src.config import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file processing with security validations"""
    
    def __init__(self):
        self.security_config = config.SECURITY
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate file for security and processing requirements
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            bool: True if file is valid for processing
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Validate file extension
            if not self.security_config.validate_file_extension(file_path):
                logger.warning(f"Unsupported file extension: {file_path}")
                return False
            
            # Validate file size
            file_size = os.path.getsize(file_path)
            if not self.security_config.validate_file_size(file_size):
                logger.warning(f"File too large: {file_path} ({file_size} bytes)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {str(e)}")
            return False
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """
        Read file content with security validation
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            str: File content if valid, None otherwise
        """
        try:
            if not self.validate_file(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            logger.info(f"Successfully read file: {file_path}")
            return content
            
        except UnicodeDecodeError:
            logger.warning(f"Could not decode file as UTF-8: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def chunk_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split content into overlapping chunks for better retrieval
        
        Args:
            content: Text content to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List[str]: List of content chunks
        """
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at a natural boundary (newline)
            if end < len(content):
                # Look for the last newline in the chunk
                last_newline = content.rfind('\n', start, end)
                if last_newline > start:
                    end = last_newline + 1
            
            chunk = content[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(content):
                break
        
        logger.info(f"Created {len(chunks)} chunks from content")
        return chunks
    
    def get_file_metadata(self, file_path: str) -> Dict[str, str]:
        """
        Extract metadata from file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict[str, str]: File metadata
        """
        try:
            stat = os.stat(file_path)
            return {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': str(stat.st_size),
                'file_extension': Path(file_path).suffix,
                'last_modified': str(stat.st_mtime),
                'file_hash': self._calculate_file_hash(file_path)
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {str(e)}")
            return {}
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for integrity checking"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[str]:
        """
        Scan directory for valid code files
        
        Args:
            directory_path: Path to directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List[str]: List of valid file paths
        """
        valid_files = []
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    # Skip common directories that shouldn't be processed
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.validate_file(file_path):
                            valid_files.append(file_path)
            else:
                for file in os.listdir(directory_path):
                    file_path = os.path.join(directory_path, file)
                    if os.path.isfile(file_path) and self.validate_file(file_path):
                        valid_files.append(file_path)
        
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {str(e)}")
        
        logger.info(f"Found {len(valid_files)} valid files in {directory_path}")
        return valid_files

# Global file processor instance
file_processor = FileProcessor() 