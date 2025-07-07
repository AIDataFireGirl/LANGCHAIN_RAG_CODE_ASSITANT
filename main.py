#!/usr/bin/env python3
"""
Main entry point for RAG Code Assistant
Provides command-line interface and server startup
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config import config
from src.embeddings.embedding_manager import embedding_manager
from src.assistant.code_assistant import code_assistant

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_setup():
    """Validate that the system is properly set up"""
    try:
        # Validate configuration
        config.validate_configuration()
        logger.info("✅ Configuration validated successfully")
        
        # Test OpenAI connection
        if not config.OPENAI.is_configured():
            logger.error("❌ OpenAI API key not configured")
            return False
        
        logger.info("✅ OpenAI configuration validated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup validation failed: {str(e)}")
        return False

def embed_codebase_cli(directory_path: str):
    """Embed codebase from command line"""
    try:
        logger.info(f"🔍 Scanning directory: {directory_path}")
        
        if not os.path.exists(directory_path):
            logger.error(f"❌ Directory does not exist: {directory_path}")
            return False
        
        success = embedding_manager.embed_codebase(directory_path)
        
        if success:
            stats = embedding_manager.get_collection_stats()
            logger.info(f"✅ Codebase embedded successfully!")
            logger.info(f"📊 Files processed: {stats.get('total_documents', 0)}")
            return True
        else:
            logger.error("❌ Failed to embed codebase")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error embedding codebase: {str(e)}")
        return False

def interactive_mode():
    """Run in interactive mode for command-line queries"""
    try:
        logger.info("🤖 Starting interactive mode...")
        logger.info("💡 Type 'quit' to exit")
        
        while True:
            try:
                question = input("\n❓ Ask a question about your code: ")
                
                if question.lower() in ['quit', 'exit', 'q']:
                    logger.info("👋 Goodbye!")
                    break
                
                if not question.strip():
                    continue
                
                logger.info("🤔 Processing your question...")
                response = code_assistant.ask_question(question)
                
                if response.get('error'):
                    logger.error(f"❌ Error: {response['error']}")
                else:
                    print(f"\n🤖 Answer: {response['answer']}")
                    
                    if response.get('sources'):
                        print(f"\n📚 Sources ({len(response['sources'])}):")
                        for i, source in enumerate(response['sources'], 1):
                            print(f"  {i}. {source['metadata'].get('file_name', 'Unknown file')}")
                
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"❌ Error processing question: {str(e)}")
                
    except Exception as e:
        logger.error(f"❌ Error in interactive mode: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RAG Code Assistant - AI-powered code analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Embed a codebase
  python main.py embed /path/to/your/codebase
  
  # Start interactive mode
  python main.py interactive
  
  # Start API server
  python main.py serve
  
  # Start web interface
  python main.py web
        """
    )
    
    parser.add_argument(
        'command',
        choices=['embed', 'interactive', 'serve', 'web', 'health'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        help='Directory path for embed command'
    )
    
    args = parser.parse_args()
    
    # Validate setup
    if not validate_setup():
        logger.error("❌ Setup validation failed. Please check your configuration.")
        sys.exit(1)
    
    try:
        if args.command == 'embed':
            if not args.directory:
                logger.error("❌ Directory path is required for embed command")
                sys.exit(1)
            
            success = embed_codebase_cli(args.directory)
            sys.exit(0 if success else 1)
            
        elif args.command == 'interactive':
            interactive_mode()
            
        elif args.command == 'serve':
            logger.info("🚀 Starting API server...")
            import uvicorn
            uvicorn.run(
                "src.api.routes:app",
                host=config.HOST,
                port=config.PORT,
                reload=config.DEBUG
            )
            
        elif args.command == 'web':
            logger.info("🌐 Starting web interface...")
            import subprocess
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", "src/web/streamlit_app.py"
            ])
            
        elif args.command == 'health':
            logger.info("🏥 Checking system health...")
            stats = embedding_manager.get_collection_stats()
            info = code_assistant.get_system_info()
            
            print(f"✅ OpenAI configured: {config.OPENAI.is_configured()}")
            print(f"📊 Documents in vector store: {stats.get('total_documents', 0)}")
            print(f"🤖 Model: {info.get('model_name', 'Unknown')}")
            print(f"💬 Conversation history: {info.get('conversation_history_length', 0)} messages")
            
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 