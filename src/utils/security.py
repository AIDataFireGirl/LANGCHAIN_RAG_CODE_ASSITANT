"""
Security utilities for RAG Code Assistant
Provides additional guard rails and validation functions
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Security validation and guard rails for the RAG Code Assistant"""
    
    def __init__(self):
        # Define potentially harmful patterns
        self.harmful_patterns = [
            r'\b(exec|eval|compile|__import__)\s*\(',
            r'\b(os|subprocess|sys)\s*\.',
            r'\b(open|file|read|write)\s*\(',
            r'\b(delete|remove|rm|del)\s+',
            r'\b(system|popen|call)\s*\(',
            r'\b(import\s+os|import\s+sys|import\s+subprocess)',
            r'\b(while\s+True|for\s+.*\s+in\s+.*:)',  # Potential infinite loops
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.harmful_patterns]
        
        # Rate limiting
        self.request_counts = {}
        self.max_requests_per_minute = 60
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate user query for security concerns
        
        Args:
            query: User query to validate
            
        Returns:
            Dict[str, Any]: Validation result with is_safe and reason
        """
        try:
            # Check for harmful patterns
            for pattern in self.compiled_patterns:
                if pattern.search(query):
                    return {
                        'is_safe': False,
                        'reason': f'Query contains potentially harmful content: {pattern.pattern}',
                        'pattern': pattern.pattern
                    }
            
            # Check for excessive length
            if len(query) > 1000:
                return {
                    'is_safe': False,
                    'reason': 'Query is too long (max 1000 characters)',
                    'length': len(query)
                }
            
            # Check for suspicious keywords
            suspicious_keywords = [
                'password', 'secret', 'key', 'token', 'credential',
                'admin', 'root', 'sudo', 'privilege', 'elevate'
            ]
            
            query_lower = query.lower()
            found_keywords = [kw for kw in suspicious_keywords if kw in query_lower]
            
            if found_keywords:
                logger.warning(f"Suspicious keywords found in query: {found_keywords}")
                return {
                    'is_safe': False,
                    'reason': f'Query contains suspicious keywords: {", ".join(found_keywords)}',
                    'keywords': found_keywords
                }
            
            return {
                'is_safe': True,
                'reason': 'Query passed security validation'
            }
            
        except Exception as e:
            logger.error(f"Error validating query: {str(e)}")
            return {
                'is_safe': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    def validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file path for security
        
        Args:
            file_path: File path to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        try:
            path = Path(file_path)
            
            # Check for path traversal attempts
            if '..' in str(path):
                return {
                    'is_safe': False,
                    'reason': 'Path traversal attempt detected'
                }
            
            # Check for absolute paths outside allowed directories
            if path.is_absolute():
                # Add your allowed directories here
                allowed_dirs = ['/home', '/Users', '/tmp', '/var/tmp']
                if not any(str(path).startswith(allowed) for allowed in allowed_dirs):
                    return {
                        'is_safe': False,
                        'reason': 'Path outside allowed directories'
                    }
            
            # Check for suspicious file extensions
            suspicious_extensions = ['.exe', '.bat', '.cmd', '.sh', '.ps1']
            if path.suffix.lower() in suspicious_extensions:
                return {
                    'is_safe': False,
                    'reason': f'Suspicious file extension: {path.suffix}'
                }
            
            return {
                'is_safe': True,
                'reason': 'File path passed security validation'
            }
            
        except Exception as e:
            logger.error(f"Error validating file path: {str(e)}")
            return {
                'is_safe': False,
                'reason': f'Path validation error: {str(e)}'
            }
    
    def sanitize_input(self, input_text: str) -> str:
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            input_text: Text to sanitize
            
        Returns:
            str: Sanitized text
        """
        try:
            # Remove or escape potentially dangerous characters
            sanitized = input_text.strip()
            
            # Remove null bytes
            sanitized = sanitized.replace('\x00', '')
            
            # Limit length
            if len(sanitized) > 1000:
                sanitized = sanitized[:1000]
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing input: {str(e)}")
            return ""
    
    def check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """
        Check rate limiting for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict[str, Any]: Rate limit status
        """
        import time
        
        current_time = time.time()
        
        if user_id not in self.request_counts:
            self.request_counts[user_id] = []
        
        # Remove old requests (older than 1 minute)
        self.request_counts[user_id] = [
            req_time for req_time in self.request_counts[user_id]
            if current_time - req_time < 60
        ]
        
        # Check if user has exceeded rate limit
        if len(self.request_counts[user_id]) >= self.max_requests_per_minute:
            return {
                'allowed': False,
                'reason': 'Rate limit exceeded',
                'requests_in_last_minute': len(self.request_counts[user_id])
            }
        
        # Add current request
        self.request_counts[user_id].append(current_time)
        
        return {
            'allowed': True,
            'requests_in_last_minute': len(self.request_counts[user_id])
        }
    
    def validate_file_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Validate file content for security
        
        Args:
            content: File content to validate
            file_path: Path to the file
            
        Returns:
            Dict[str, Any]: Validation result
        """
        try:
            # Check for suspicious content patterns
            suspicious_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'private_key',
                r'BEGIN\s+PRIVATE\s+KEY',
                r'BEGIN\s+RSA\s+PRIVATE\s+KEY',
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    logger.warning(f"Suspicious content found in {file_path}")
                    return {
                        'is_safe': False,
                        'reason': f'Suspicious content pattern detected: {pattern}',
                        'pattern': pattern
                    }
            
            # Check for binary content
            try:
                content.encode('utf-8')
            except UnicodeEncodeError:
                return {
                    'is_safe': False,
                    'reason': 'File appears to be binary or contains invalid characters'
                }
            
            return {
                'is_safe': True,
                'reason': 'File content passed security validation'
            }
            
        except Exception as e:
            logger.error(f"Error validating file content: {str(e)}")
            return {
                'is_safe': False,
                'reason': f'Content validation error: {str(e)}'
            }
    
    def generate_file_hash(self, file_path: str) -> str:
        """
        Generate SHA-256 hash of file for integrity checking
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: SHA-256 hash
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Error generating file hash: {str(e)}")
            return ""
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log security events for monitoring
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        logger.warning(f"SECURITY EVENT - {event_type}: {details}")

# Global security validator instance
security_validator = SecurityValidator() 