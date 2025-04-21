"""
Configuration for the embedding service.
"""
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('embedding-service')

# Database connection configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'dbname': os.environ.get('DB_NAME', 'trace'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', '')
}

# Embedding configuration
EMBEDDING_CONFIG = {
    'model_name': os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
    'embedding_dim': int(os.environ.get('EMBEDDING_DIM', '384')),  # Dimension for all-MiniLM-L6-v2
    'batch_size': int(os.environ.get('BATCH_SIZE', '32')),
    'max_retries': int(os.environ.get('MAX_RETRIES', '3')),
    'retry_delay': int(os.environ.get('RETRY_DELAY', '5')),  # seconds
    'schema': {
        'vector': os.environ.get('VECTOR_SCHEMA', 'vectors'),
        'source': os.environ.get('SOURCE_SCHEMA', 'trace'),
    },
    'tables': {
        'comment': os.environ.get('COMMENT_EMBEDDING_TABLE', 'comment_embeddings'),
        'rating': os.environ.get('RATING_EMBEDDING_TABLE', 'rating_embeddings'),
        'instructor': os.environ.get('INSTRUCTOR_EMBEDDING_TABLE', 'instructor_embeddings'),
        'course': os.environ.get('COURSE_EMBEDDING_TABLE', 'course_embeddings'),
    }
}