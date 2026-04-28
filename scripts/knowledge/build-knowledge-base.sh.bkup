#!/bin/bash
#
# Knowledge Base Builder for AI Cycling Coach
# Processes training knowledge files and loads into PostgreSQL with embeddings
#

set -e  # Exit on any error

# Configuration
KNOWLEDGE_DIR="/root/ai-cycling-coach/data/knowledge-base"
DB_CONTAINER="ai-cycling-coach-postgres-1"
DB_NAME="aicoach_db"
DB_USER="aicoach_user"
OLLAMA_URL="http://localhost:11434/api/embeddings"
EMBEDDING_MODEL="nomic-embed-text"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Cycling Coach - Knowledge Base Builder               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to chunk text
chunk_text() {
    local file="$1"
    local source="$2"
    local chunk_size=3000  # ~500 tokens (1 token ≈ 4 chars)
    
    echo -e "${YELLOW}📄 Processing: $(basename "$file")${NC}"
    
    # Read file and split by markdown headers or paragraphs
    awk -v chunk_size="$chunk_size" '
    BEGIN { 
        chunk = ""
        in_section = 0
    }
    
    # On markdown header (## or ###), finish previous chunk and start new
    /^#{2,3} / {
        # Save previous chunk if substantial
        if (length(chunk) > 200) {
            print chunk
            print "---CHUNK_SEPARATOR---"
        }
        # Start new chunk with header
        chunk = $0 "\n"
        in_section = 1
        next
    }
    
    # Skip empty lines at start of chunk
    /^[[:space:]]*$/ {
        if (length(chunk) < 10) next
    }
    
    # Accumulate content
    {
        chunk = chunk $0 "\n"
        
        # If chunk is large enough AND we hit a paragraph break, save it
        if (length(chunk) >= chunk_size && /^[[:space:]]*$/) {
            print chunk
            print "---CHUNK_SEPARATOR---"
            chunk = ""
        }
    }
    
    # Save final chunk
    END {
        if (length(chunk) > 200) {
            print chunk
        }
    }
    ' "$file"
    
}

# Function to generate embedding
generate_embedding() {
    local text="$1"
    
    # Escape text for JSON
    local escaped_text=$(echo "$text" | jq -Rs .)
    
    # Call Ollama API
    curl -s "$OLLAMA_URL" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$EMBEDDING_MODEL\", \"prompt\": $escaped_text}" \
        | jq -c '.embedding'
}

# Function to insert into database
insert_chunk() {
    local content="$1"
    local embedding="$2"
    local source="$3"
    
    # Escape content for SQL
    local escaped_content=$(echo "$content" | sed "s/'/''/g")
    
    # Insert into database
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << EOF
INSERT INTO training_knowledge (content, embedding, source, metadata)
VALUES (
    E'$escaped_content',
    '$embedding',
    '$source',
    '{}'
);
EOF
}

# Main processing loop
echo -e "${GREEN}📁 Scanning knowledge base directory...${NC}"
echo ""

total_chunks=0

# Process each file in knowledge base
for file in "$KNOWLEDGE_DIR"/*.{md,txt}; do
    # Skip if no files match
    [ -e "$file" ] || continue
    # Skip README files
    if [[ "$(basename "$file")" =~ ^README ]]; then
        echo -e "${YELLOW}⏩ Skipping: $(basename "$file") (documentation)${NC}"
        continue
    fi
    # Get source name from filename
    source=$(basename "$file" | sed 's/\.[^.]*$//')
    
    echo -e "${BLUE}Processing: $source${NC}"
    
    # Chunk the file
    chunks=$(chunk_text "$file" "$source")
    
    # Process each chunk
    chunk_num=0
    echo "$chunks" | while IFS= read -r chunk; do
        # Skip separator lines
        if [ "$chunk" = "---CHUNK_SEPARATOR---" ]; then
            continue
        fi
        
        # Skip empty chunks
        if [ -z "$(echo "$chunk" | tr -d '[:space:]')" ]; then
            continue
        fi
        
        chunk_num=$((chunk_num + 1))
        echo -ne "  Chunk $chunk_num: Generating embedding... "
        
        # Generate embedding
        embedding=$(generate_embedding "$chunk")
        
        if [ -z "$embedding" ] || [ "$embedding" = "null" ]; then
            echo -e "${YELLOW}SKIP (no embedding)${NC}"
            continue
        fi
        
        echo -ne "Storing... "
        
        # Insert into database
        insert_chunk "$chunk" "$embedding" "$source"
        
        echo -e "${GREEN}✓${NC}"
        
        total_chunks=$((total_chunks + 1))
        
        # Small delay to not overwhelm Ollama
        sleep 0.2
    done
    
    echo ""
done

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 ✓ Knowledge Base Built!                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get statistics
echo -e "${BLUE}📊 Database Statistics:${NC}"
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT 
    source,
    COUNT(*) as chunks
FROM training_knowledge
GROUP BY source
ORDER BY chunks DESC;

SELECT COUNT(*) as total_chunks FROM training_knowledge;
EOF

echo ""
echo -e "${GREEN}✅ Knowledge base is ready for RAG!${NC}"
