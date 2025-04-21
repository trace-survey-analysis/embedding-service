import psycopg2
import argparse
from sentence_transformers import SentenceTransformer
from config import DB_CONFIG, EMBEDDING_CONFIG, logger
from create_embeddings import (
    generate_comment_embeddings, 
    generate_rating_embeddings,
    generate_instructor_embeddings,
    generate_course_embeddings,
    test_similarity_search,
    mark_all_for_embedding
)

def main():
    """Main function for pgvector embeddings."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate embeddings for trace data')
    parser.add_argument('--rebuild', action='store_true', help='Rebuild all embeddings from scratch')
    parser.add_argument('--test', action='store_true', help='Only run the similarity search test')
    parser.add_argument('--comments', action='store_true', help='Only process comments')
    parser.add_argument('--ratings', action='store_true', help='Only process ratings')
    parser.add_argument('--instructors', action='store_true', help='Only process instructors')
    parser.add_argument('--courses', action='store_true', help='Only process courses')
    args = parser.parse_args()
    
    # Load the embedding model
    logger.info("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_CONFIG['model_name'])
    logger.info(f"Model {EMBEDDING_CONFIG['model_name']} loaded successfully")
    
    # Connect to database
    logger.info("Connecting to PostgreSQL...")
    conn = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to database successfully")
        
        # Mark all records for embedding if rebuild flag is set
        if args.rebuild:
            mark_all_for_embedding(conn)
            logger.info("Marked all records for embedding regeneration")
        
        # If test flag is set, only run the similarity search test
        if args.test:
            logger.info("Running similarity test only...")
            test_similarity_search(conn, model)
            return
        
        # Process each content type based on arguments or process all if none specified
        process_all = not any([args.comments, args.ratings, args.instructors, args.courses])
        
        # Track total processed counts
        total_processed = 0
        
        if process_all or args.comments:
            num_comments = generate_comment_embeddings(conn, model)
            logger.info(f"Generated embeddings for {num_comments} comments")
            total_processed += num_comments
        
        if process_all or args.ratings:
            num_ratings = generate_rating_embeddings(conn, model)
            logger.info(f"Generated embeddings for {num_ratings} ratings")
            total_processed += num_ratings
        
        if process_all or args.instructors:
            num_instructors = generate_instructor_embeddings(conn, model)
            logger.info(f"Generated embeddings for {num_instructors} instructors")
            total_processed += num_instructors
        
        if process_all or args.courses:
            num_courses = generate_course_embeddings(conn, model)
            logger.info(f"Generated embeddings for {num_courses} courses")
            total_processed += num_courses
        
        # Test similarity search if we generated any embeddings
        if total_processed > 0:
            logger.info("Testing similarity search...")
            test_similarity_search(conn, model)
    
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    
    finally:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed")
        logger.info("Process completed")

if __name__ == "__main__":
    main()