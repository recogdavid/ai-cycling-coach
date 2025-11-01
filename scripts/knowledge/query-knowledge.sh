#!/bin/bash
#
# Query Knowledge Base for RAG
# Usage: ./query-knowledge.sh "your query here" [top_k]
#

set -e

# Configuration
DB_CONTAINER="ai-cycling-coach-postgres-1"
DB_NAME="aicoach_db"
DB_USER="aicoach_user"
OLLAMA_URL="http://localhost:11434/api/embeddings"
EMBEDDING_MODEL="nomic-embed-text"

# Parse arguments
QUERY="$1"
TOP_K="${2:-5}"  # Default to 5 results

if [ -z "$QUERY" ]; then
    echo "Usage: $0 'your query' [top_k]"
    echo "Example: $0 'threshold workout structures' 5"
    exit 1
fi

# Generate embedding for query
echo "🔍 Querying: $QUERY" >&2
echo "Generating embedding..." >&2

ESCAPED_QUERY=$(echo "$QUERY" | jq -Rs .)
EMBEDDING=$(curl -s "$OLLAMA_URL" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"$EMBEDDING_MODEL\", \"prompt\": $ESCAPED_QUERY}" \
    | jq -c '.embedding')

if [ -z "$EMBEDDING" ] || [ "$EMBEDDING" = "null" ]; then
    echo "Error: Failed to generate embedding" >&2
    exit 1
fi

echo "Searching knowledge base..." >&2

# Query database for similar vectors
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t << EOF
SELECT 
    json_build_object(
        'content', content,
        'source', source,
        'similarity', ROUND((1 - (embedding <=> '$EMBEDDING'::vector))::numeric, 3)
    )
FROM training_knowledge
WHERE 1 - (embedding <=> '$EMBEDDING'::vector) > 0.5
ORDER BY embedding <=> '$EMBEDDING'::vector
LIMIT $TOP_K;
EOF
