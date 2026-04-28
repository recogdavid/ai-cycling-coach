#!/bin/bash
DB_CONTAINER="ai-cycling-coach-postgres-1"
DB_NAME="aicoach_db"
DB_USER="aicoach_user"
OLLAMA_URL="http://localhost:11434/api/embeddings"
EMBEDDING_MODEL="nomic-embed-text"

# Get all messages needing embeddings
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -F'|' \
  -c "SELECT id, content FROM chat_messages WHERE embedding IS NULL AND role = 'user' AND content IS NOT NULL AND TRIM(content) != '' ORDER BY id;" \
  | while IFS='|' read -r id content; do
    
    echo "Processing id=$id"
    
    # Escape text for JSON
    escaped_text=$(echo "$content" | jq -Rs .)
    
    # Generate embedding
    embedding=$(curl -s "$OLLAMA_URL" \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"$EMBEDDING_MODEL\", \"prompt\": $escaped_text}" \
      | jq -c '.embedding')
    
    [[ -z "$embedding" || "$embedding" == "null" ]] && {
      echo "WARN: No embedding for id=$id"
      continue
    }
    
    # Store directly
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" \
      -c "UPDATE chat_messages SET embedding = '$embedding'::vector WHERE id = $id;"
    
    echo "Done id=$id"
done
