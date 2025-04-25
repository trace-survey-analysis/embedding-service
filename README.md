# Embedding Service

![Python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)
![Jenkins](https://img.shields.io/badge/Jenkins-D24939.svg?style=for-the-badge&logo=jenkins&logoColor=white)
![Semantic Release](https://img.shields.io/badge/Semantic_Release-494949.svg?style=for-the-badge&logo=semantic-release&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E.svg?style=for-the-badge&logo=huggingface&logoColor=black)

A service for generating and managing vector embeddings for TRACE survey data, enabling semantic search and similarity analysis.

## Overview

The Embedding Service is a critical component of the trace-survey-analysis platform that:

1. Extracts textual data from processed TRACE surveys in the PostgreSQL database
2. Generates vector embeddings using state-of-the-art transformer models
3. Stores embeddings in a vector database (PostgreSQL with pgvector extension)
4. Enables semantic search and similarity analysis across survey data

This service transforms raw text data into multidimensional vector representations that capture semantic meaning, allowing for powerful natural language processing capabilities such as finding similar comments, ratings, courses, or instructors based on semantic similarity rather than just keyword matching.

## Architecture

The embedding service consists of the following components:

### Core Components

- **Embedding Generator**: Uses sentence-transformers to convert text into vector embeddings
- **Database Connector**: Manages connections to PostgreSQL and handles vector storage
- **Processing Pipeline**: Processes different types of data (comments, ratings, instructors, courses)
- **Similarity Search**: Tests and verifies vector similarity functionality

### Data Flow

1. The service connects to the PostgreSQL database containing TRACE survey data
2. It identifies records that need embedding generation (marked with `embedding_needed = TRUE`)
3. For each record, it extracts relevant text and sends it to the transformer model
4. The model generates a vector embedding (default: 384-dimensional vector)
5. The embedding is stored in the corresponding table in the `vectors` schema
6. The original record is marked as processed (`embedding_needed = FALSE`)

## Database Schema

The service operates on two PostgreSQL schemas:

1. **trace schema**: Contains the raw data from processed TRACE surveys (from [trace-consumer](https://github.com/cyse7125-sp25-team03/trace-consumer.git))
   - `comments`: Student comments on courses and instructors
   - `ratings`: Numerical ratings for various questions
   - `instructors`: Information about course instructors
   - `courses`: Course information

2. **vectors schema**: Contains the generated embeddings (created by [db-trace-processor](https://github.com/cyse7125-sp25-team03/db-trace-processor.git))
   - `comment_embeddings`: Vector embeddings for student comments
   - `rating_embeddings`: Vector embeddings for rating questions
   - `instructor_embeddings`: Vector embeddings for instructor information
   - `course_embeddings`: Vector embeddings for course information

The database migrations for these schemas are managed by the [db-trace-processor](https://github.com/cyse7125-sp25-team03/db-trace-processor.git) repository.

## Prerequisites

- Python 3.8+
- PostgreSQL 14+ with pgvector extension
- Database schema set up using [db-trace-processor](https://github.com/cyse7125-sp25-team03/db-trace-processor.git)
- TRACE survey data loaded from [trace-consumer](https://github.com/cyse7125-sp25-team03/trace-consumer.git)

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/cyse7125-sp25-team03/embedding-service.git
   cd embedding-service
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (create a `.env` file):
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=trace
   DB_USER=postgres
   DB_PASSWORD=your_password
   
   # Optional: customize embedding settings
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   EMBEDDING_DIM=384
   BATCH_SIZE=32
   ```

### Docker Deployment

```bash
docker build -t embedding-service .
docker run -d --name embedding-service \
  --env-file .env \
  embedding-service
```

## Usage

The embedding service can be run with various command-line arguments to control its behavior:

```bash
python main.py [options]
```

### Command-line Options

| Option | Description |
|--------|-------------|
| `--rebuild` | Rebuild all embeddings from scratch |
| `--test` | Only run the similarity search test |
| `--comments` | Only process comments |
| `--ratings` | Only process ratings |
| `--instructors` | Only process instructors |
| `--courses` | Only process courses |

### Examples

Process only new items (that haven't been embedded yet):
```bash
python main.py
```

Rebuild all embeddings from scratch:
```bash
python main.py --rebuild
```

Process only comments and ratings:
```bash
python main.py --comments --ratings
```

Run only the similarity search test:
```bash
python main.py --test
```

## Embedding Models

The service uses pre-trained transformer models from the [sentence-transformers](https://www.sbert.net/) library to generate embeddings:

- Default model: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- The model can be customized by setting the `EMBEDDING_MODEL` environment variable

### How Embeddings Are Generated

Different types of data are embedded in specific ways to capture their semantic meaning:

1. **Comments**:
   - Format: `"Question: {question_text}. Comment: {comment_text}. Category: {category}"`
   - Example: `"Question: What did you like most about this course? Comment: The professor was very knowledgeable and engaging. Category: Positive"`

2. **Ratings**:
   - Format: `"Question: {question_text}. Category: {category}. Score: {course_mean}/5.0"`
   - Example: `"Question: The instructor was well prepared for class. Category: Preparation. Score: 4.7/5.0"`

3. **Instructors**:
   - Format: `"Instructor: {name}. Teaches courses: {courses_list}"`
   - Example: `"Instructor: John Smith. Teaches courses: CS101: Intro to Programming (Fall 2023) | CS201: Data Structures (Spring 2024)"`

4. **Courses**:
   - Format: `"Course code: {course_code} Course name: {course_name}. Subject: {subject}. Section: {catalog_section}. Term: {semester} {year}. Enrollment: {enrollment} students, {responses} responses. Instructors: {instructors_list}"`
   - Example: `"Course code: CS101 Course name: Introduction to Programming. Subject: Computer Science. Section: 001. Term: Fall 2023. Enrollment: 150 students, 120 responses. Instructors: John Smith, Jane Doe"`

## Vector Similarity Search

Once embeddings are generated, they can be used for semantic search using PostgreSQL's pgvector extension. Examples of similarity searches:

- Find comments similar to a given comment
- Find instructors teaching subjects similar to a search query
- Find courses similar to a description or subject area

The service includes a test function that demonstrates similarity searches across all embedding types.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `trace` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASSWORD` | Database password | `""` |
| `EMBEDDING_MODEL` | Transformer model name | `all-MiniLM-L6-v2` |
| `EMBEDDING_DIM` | Embedding dimensions | `384` |
| `BATCH_SIZE` | Processing batch size | `32` |
| `MAX_RETRIES` | Max retries for failed embeddings | `3` |
| `RETRY_DELAY` | Delay between retries (seconds) | `5` |
| `VECTOR_SCHEMA` | Schema for vector tables | `vectors` |
| `SOURCE_SCHEMA` | Schema for source data | `trace` |

## Deployment with Helm

The embedding-service can be deployed to Kubernetes using the Helm chart available at [helm-charts repository](https://github.com/cyse7125-sp25-team03/helm-charts.git) in the `embedding-service` folder.

```bash
# Clone the helm-charts repository
git clone https://github.com/cyse7125-sp25-team03/helm-charts.git
cd helm-charts

# Install the embedding-service chart in the postgres namespace
helm install embedding-service ./embedding-service/ -n postgres
```

## CI/CD

This project uses Jenkins for continuous integration and Semantic Release for versioning:

- When a pull request is successfully merged, a Docker image is built
- The Semantic Versioning bot creates a release on GitHub with a tag
- The tagged release is used for the Docker image, which is then pushed to Docker Hub

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check that PostgreSQL is running and accessible
   - Verify database credentials are correct
   - Ensure pgvector extension is installed

2. **Missing pgvector Extension**
   - Install pgvector in PostgreSQL in the public schema: `CREATE EXTENSION vector;`
   - Verify with: `SELECT * FROM pg_extension WHERE extname = 'vector';`
   - Note: The extension must be created in the public schema, but it can be used from any schema including the vectors schema

3. **Model Loading Errors**
   - Ensure internet connectivity to download model files
   - Check for sufficient disk space for model storage
   - Consider using a smaller model if memory constraints exist

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.