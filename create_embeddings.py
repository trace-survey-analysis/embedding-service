import psycopg2
from sentence_transformers import SentenceTransformer
import time
from config import DB_CONFIG, EMBEDDING_CONFIG, logger

def generate_comment_embeddings(conn, model):
    """Generate embeddings for comments that need them."""
    cursor = conn.cursor()
    
    try:
        # Get comments that need embeddings
        cursor.execute("""
            SELECT id, question_text, comment_text, category
            FROM trace.comments
            WHERE embedding_needed IS NULL OR embedding_needed = TRUE;
        """)
        
        comments = cursor.fetchall()
        logger.info(f"Found {len(comments)} comments to process")
        processed_count = 0
        
        for comment_id, question_text, comment_text, category in comments:
            try:
                # Generate text for embedding
                text = f"Question: {question_text}. Comment: {comment_text}. Category: {category}"
                
                # Generate embedding with retry logic
                retry_count = 0
                while retry_count < EMBEDDING_CONFIG['max_retries']:
                    try:
                        embedding = model.encode(text).tolist()
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"Retry {retry_count}/{EMBEDDING_CONFIG['max_retries']} for comment ID {comment_id}: {e}")
                        if retry_count >= EMBEDDING_CONFIG['max_retries']:
                            raise
                        time.sleep(EMBEDDING_CONFIG['retry_delay'])
                
                # Store embedding in vectors schema
                cursor.execute("""
                    INSERT INTO vectors.comment_embeddings (comment_id, embedding)
                    VALUES (%s, %s)
                    ON CONFLICT (comment_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding, 
                        created_at = CURRENT_TIMESTAMP;
                """, (comment_id, embedding))
                
                # Mark as processed
                cursor.execute("""
                    UPDATE trace.comments
                    SET embedding_needed = FALSE
                    WHERE id = %s;
                """, (comment_id,))
                
                processed_count += 1
                logger.info(f"Processed comment ID: {comment_id}")
                
                # Commit after each successful embedding to prevent losing progress
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error processing comment ID {comment_id}: {e}")
                # Continue with next comment instead of failing the entire batch
        
        return processed_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in comment embedding generation: {e}")
        return 0
    
    finally:
        cursor.close()

def generate_rating_embeddings(conn, model):
    """Generate embeddings for ratings that need them."""
    cursor = conn.cursor()
    
    try:
        # Get ratings that need embeddings
        cursor.execute("""
            SELECT id, question_text, category, course_mean
            FROM trace.ratings
            WHERE embedding_needed IS NULL OR embedding_needed = TRUE;
        """)
        
        ratings = cursor.fetchall()
        logger.info(f"Found {len(ratings)} ratings to process")
        processed_count = 0
        
        for rating_id, question_text, category, course_mean in ratings:
            try:
                # Generate text for embedding - include score for better semantic understanding
                text = f"Question: {question_text}. Category: {category}. Score: {course_mean}/5.0"
                
                # Generate embedding with retry logic
                retry_count = 0
                while retry_count < EMBEDDING_CONFIG['max_retries']:
                    try:
                        embedding = model.encode(text).tolist()
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"Retry {retry_count}/{EMBEDDING_CONFIG['max_retries']} for rating ID {rating_id}: {e}")
                        if retry_count >= EMBEDDING_CONFIG['max_retries']:
                            raise
                        time.sleep(EMBEDDING_CONFIG['retry_delay'])
                
                # Store embedding in vectors schema
                cursor.execute("""
                    INSERT INTO vectors.rating_embeddings (rating_id, embedding)
                    VALUES (%s, %s)
                    ON CONFLICT (rating_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding, 
                        created_at = CURRENT_TIMESTAMP;
                """, (rating_id, embedding))
                
                # Mark as processed
                cursor.execute("""
                    UPDATE trace.ratings
                    SET embedding_needed = FALSE
                    WHERE id = %s;
                """, (rating_id,))
                
                processed_count += 1
                logger.info(f"Processed rating ID: {rating_id}")
                
                # Commit after each successful embedding to prevent losing progress
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error processing rating ID {rating_id}: {e}")
                # Continue with next rating instead of failing the entire batch
        
        return processed_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in rating embedding generation: {e}")
        return 0
    
    finally:
        cursor.close()

def generate_instructor_embeddings(conn, model):
    """Generate embeddings for instructors."""
    cursor = conn.cursor()
    
    try:
        # Get all instructors with their courses
        cursor.execute("""
            SELECT i.id, i.name, 
                   string_agg(DISTINCT c.course_id || ': ' || c.course_name || ' (' || c.semester || ' ' || c.year || ')', ' | ') as courses
            FROM trace.instructors i
            LEFT JOIN trace.course_instructors ci ON i.id = ci.instructor_id
            LEFT JOIN trace.courses c ON ci.course_id = c.id
            WHERE i.embedding_needed IS NULL OR i.embedding_needed = TRUE
            GROUP BY i.id, i.name;
        """)
        
        instructors = cursor.fetchall()
        logger.info(f"Found {len(instructors)} instructors to process")
        processed_count = 0
        
        for instructor_id, name, courses in instructors:
            try:
                # Generate text for embedding
                text = f"Instructor: {name}. Teaches courses: {courses or 'None'}"
                
                # Generate embedding with retry logic
                retry_count = 0
                while retry_count < EMBEDDING_CONFIG['max_retries']:
                    try:
                        embedding = model.encode(text).tolist()
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"Retry {retry_count}/{EMBEDDING_CONFIG['max_retries']} for instructor ID {instructor_id}: {e}")
                        if retry_count >= EMBEDDING_CONFIG['max_retries']:
                            raise
                        time.sleep(EMBEDDING_CONFIG['retry_delay'])
                
                # Store embedding in vectors schema
                cursor.execute("""
                    INSERT INTO vectors.instructor_embeddings (instructor_id, embedding)
                    VALUES (%s, %s)
                    ON CONFLICT (instructor_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding, 
                        created_at = CURRENT_TIMESTAMP;
                """, (instructor_id, embedding))
                
                # Mark as processed
                cursor.execute("""
                    UPDATE trace.instructors
                    SET embedding_needed = FALSE
                    WHERE id = %s;
                """, (instructor_id,))
                
                processed_count += 1
                logger.info(f"Processed instructor ID: {instructor_id}")
                
                # Commit after each successful embedding to prevent losing progress
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error processing instructor ID {instructor_id}: {e}")
                # Continue with next instructor
        
        return processed_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in instructor embedding generation: {e}")
        return 0
    
    finally:
        cursor.close()

def generate_course_embeddings(conn, model):
    """Generate embeddings for courses."""
    cursor = conn.cursor()
    
    try:
        # Get all courses with their instructors
        cursor.execute("""
            SELECT c.id, c.course_id, c.course_name, c.subject, c.catalog_section, 
                   c.semester, c.year, c.enrollment, c.responses,
                   string_agg(DISTINCT i.name, ', ') as instructors
            FROM trace.courses c
            LEFT JOIN trace.course_instructors ci ON c.id = ci.course_id
            LEFT JOIN trace.instructors i ON ci.instructor_id = i.id
            WHERE c.embedding_needed IS NULL OR c.embedding_needed = TRUE
            GROUP BY c.id, c.course_id, c.course_name, c.subject, c.catalog_section, c.semester, c.year, c.enrollment, c.responses;
        """)
        
        courses = cursor.fetchall()
        logger.info(f"Found {len(courses)} courses to process")
        processed_count = 0
        
        for course_id, course_code, course_name, subject, catalog_section, semester, year, enrollment, responses, instructors in courses:
            try:
                # Generate text for embedding
                text = (f"Course code: {course_code} Course name: {course_name}. "
                       f"Subject: {subject}. Section: {catalog_section}. "
                       f"Term: {semester} {year}. "
                       f"Enrollment: {enrollment} students, {responses} responses. "
                       f"Instructors: {instructors or 'None'}")                
                # Generate embedding with retry logic
                retry_count = 0
                while retry_count < EMBEDDING_CONFIG['max_retries']:
                    try:
                        embedding = model.encode(text).tolist()
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"Retry {retry_count}/{EMBEDDING_CONFIG['max_retries']} for course ID {course_id}: {e}")
                        if retry_count >= EMBEDDING_CONFIG['max_retries']:
                            raise
                        time.sleep(EMBEDDING_CONFIG['retry_delay'])
                
                # Store embedding in vectors schema
                cursor.execute("""
                    INSERT INTO vectors.course_embeddings (course_id, embedding)
                    VALUES (%s, %s)
                    ON CONFLICT (course_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding, 
                        created_at = CURRENT_TIMESTAMP;
                """, (course_id, embedding))
                
                # Mark as processed
                cursor.execute("""
                    UPDATE trace.courses
                    SET embedding_needed = FALSE
                    WHERE id = %s;
                """, (course_id,))
                
                processed_count += 1
                logger.info(f"Processed course ID: {course_id}")
                
                # Commit after each successful embedding to prevent losing progress
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error processing course ID {course_id}: {e}")
                # Continue with next course
        
        return processed_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in course embedding generation: {e}")
        return 0
    
    finally:
        cursor.close()

def test_similarity_search(conn, model=None):
    """Test similarity search using pgvector."""
    cursor = conn.cursor()
    
    try:
        # Check for different types of embeddings
        tables = ['comment_embeddings', 'rating_embeddings', 'instructor_embeddings', 'course_embeddings']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM vectors.{table};")
                count = cursor.fetchone()[0]
                logger.info(f"Number of {table}: {count}")
            except Exception as e:
                logger.warning(f"Could not count {table}: {e}")
        
        # Test comment embeddings search if available
        try:
            cursor.execute("SELECT COUNT(*) FROM vectors.comment_embeddings;")
            if cursor.fetchone()[0] > 0:
                # Get a random comment embedding for testing
                cursor.execute("""
                    SELECT ce.comment_id, c.question_text, c.comment_text, c.category, ce.embedding
                    FROM vectors.comment_embeddings ce
                    JOIN trace.comments c ON ce.comment_id = c.id
                    LIMIT 1;
                """)
                
                result = cursor.fetchone()
                if result:
                    comment_id, question, comment, category, embedding = result
                    logger.info(f"Testing comment similarity search with comment ID: {comment_id}")
                    logger.info(f"Query text: {comment[:50]}...")
                    
                    # Find similar comments using vector similarity
                    cursor.execute("""
                        SELECT 
                            c.id,
                            c.question_text,
                            c.comment_text,
                            c.category,
                            1 - (ce.embedding <=> %s::vector) AS similarity
                        FROM 
                            vectors.comment_embeddings ce
                        JOIN 
                            trace.comments c ON ce.comment_id = c.id
                        WHERE 
                            ce.comment_id != %s
                        ORDER BY 
                            ce.embedding <=> %s::vector
                        LIMIT 3;
                    """, (embedding, comment_id, embedding))
                    
                    similar_comments = cursor.fetchall()
                    
                    logger.info(f"Found {len(similar_comments)} similar comments:")
                    for similar_id, similar_question, similar_comment, similar_category, similarity in similar_comments:
                        logger.info("-" * 50)
                        logger.info(f"Comment ID: {similar_id}")
                        logger.info(f"Similarity: {similarity:.4f}")
                        logger.info(f"Category: {similar_category}")
                        logger.info(f"Question: {similar_question}")
                        logger.info(f"Comment: {similar_comment[:100]}...")
        except Exception as e:
            logger.warning(f"Could not test comment similarity search: {e}")
            conn.rollback()  # Reset transaction state
        
        # Test instructor search if model is provided
        if model and 'instructor_embeddings' in tables:
            try:
                logger.info("-" * 80)
                logger.info("Testing instructor search")
                test_query = "Professor who teaches Computer Science"
                
                # Generate embedding for test query
                query_embedding = model.encode(test_query).tolist()
                
                cursor.execute("""
                    SELECT 
                        i.id,
                        i.name,
                        1 - (e.embedding <=> %s::vector) AS similarity
                    FROM 
                        vectors.instructor_embeddings e
                    JOIN 
                        trace.instructors i ON e.instructor_id = i.id
                    ORDER BY 
                        e.embedding <=> %s::vector
                    LIMIT 3;
                """, (query_embedding, query_embedding))
                
                results = cursor.fetchall()
                logger.info(f"Query: {test_query}")
                logger.info(f"Found {len(results)} similar instructors:")
                
                for id, name, similarity in results:
                    logger.info(f"Instructor ID: {id}, Name: {name}, Similarity: {similarity:.4f}")
            except Exception as e:
                logger.warning(f"Instructor search test failed: {e}")
                conn.rollback()  # Reset transaction state
        
        # Test course search if model is provided
        if model and 'course_embeddings' in tables:
            try:
                logger.info("-" * 80)
                logger.info("Testing course search")
                test_query = "Introduction to Computer Science"
                
                # Generate embedding for test query
                query_embedding = model.encode(test_query).tolist()
                
                cursor.execute("""
                    SELECT 
                        c.id,
                        c.course_id,
                        c.course_name,
                        c.subject,
                        1 - (e.embedding <=> %s::vector) AS similarity
                    FROM 
                        vectors.course_embeddings e
                    JOIN 
                        trace.courses c ON e.course_id = c.id
                    ORDER BY 
                        e.embedding <=> %s::vector
                    LIMIT 3;
                """, (query_embedding, query_embedding))
                
                results = cursor.fetchall()
                logger.info(f"Query: {test_query}")
                logger.info(f"Found {len(results)} similar courses:")
                
                for id, course_id, course_name, subject, similarity in results:
                    logger.info(f"Course ID: {id}, Code: {course_id}, Name: {course_name}, Subject: {subject}, Similarity: {similarity:.4f}")
            except Exception as e:
                logger.warning(f"Course search test failed: {e}")
                conn.rollback()  # Reset transaction state
    
    except Exception as e:
        logger.error(f"Error testing similarity search: {e}")
        conn.rollback()  # Ensure transaction is reset
    
    finally:
        cursor.close()

def mark_all_for_embedding(conn):
    """Mark all records as needing embeddings."""
    cursor = conn.cursor()
    
    try:
        # Add embedding_needed column to tables if they don't have it
        tables = ['comments', 'ratings', 'instructors', 'courses']
        
        for table in tables:
            try:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'trace' 
                    AND table_name = '{table}' 
                    AND column_name = 'embedding_needed';
                """)
                
                if not cursor.fetchone():
                    cursor.execute(f"""
                        ALTER TABLE trace.{table} 
                        ADD COLUMN IF NOT EXISTS embedding_needed BOOLEAN DEFAULT TRUE;
                    """)
                    logger.info(f"Added embedding_needed column to trace.{table}")
            except Exception as e:
                logger.warning(f"Could not add embedding_needed column to trace.{table}: {e}")
                conn.rollback()  # Reset transaction state
        
        # Mark all records as needing embeddings
        for table in tables:
            try:
                cursor.execute(f"UPDATE trace.{table} SET embedding_needed = TRUE;")
                logger.info(f"Marked all records in trace.{table} for embedding")
            except Exception as e:
                logger.warning(f"Could not mark records in trace.{table}: {e}")
                conn.rollback()  # Reset transaction state
        
        conn.commit()
        logger.info("Marked all records as needing embeddings")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error marking records for embedding: {e}")
    
    finally:
        cursor.close()