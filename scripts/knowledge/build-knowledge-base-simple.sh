#!/bin/bash
# Simple Knowledge Base Builder for AI Cycling Coach

set -e  # Exit on any error

# Configuration
KNOWLEDGE_DIR="/root/ai-cycling-coach/data/knowledge-base"
DB_CONTAINER="ai-cycling-coach-postgres-1"
DB_NAME="aicoach_db"
DB_USER="aicoach_user"
OLLAMA_URL="http://localhost:11434/api/embeddings"
EMBEDDING_MODEL="nomic-embed-text"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" >&2
}

# Check dependencies
check_deps() {
    for cmd in jq curl python3 docker; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "$cmd is not installed"
            return 1
        fi
    done
    
    if [[ ! -f /tmp/knowledge_processor.py ]]; then
        log_error "Python processor not found at /tmp/knowledge_processor.py"
        return 1
    fi
}

# Process a single file
process_file() {
    local file="$1"
    local source_name=$(basename "$file" | sed 's/\.[^.]*$//')
    
    log_info "Processing: $source_name"
    
    # Get chunks from Python
    local json_output
    if ! json_output=$(python3 /tmp/knowledge_processor.py < "$file" 2>/tmp/python_error.log); then
        log_warn "Python failed for $file"
        cat /tmp/python_error.log >&2
        echo "0"
        return 1
    fi
    
    # Check if we got output
    if [[ -z "$json_output" || "$json_output" == "[]" ]]; then
        log_warn "No chunks generated for $file"
        echo "0"
        return 0
    fi
    
    # Validate JSON
    if ! echo "$json_output" | jq -e . >/dev/null 2>&1; then
        log_error "Invalid JSON from $file"
        echo "Raw output: $json_output" >&2
        echo "0"
        return 1
    fi
    
    # Process each chunk
    local chunk_count=0
    while IFS= read -r chunk; do
        local text=$(echo "$chunk" | jq -r '.text // ""')
        local metadata=$(echo "$chunk" | jq -r '.metadata // "{}"')
        
        [[ -z "$text" ]] && continue
        
        # Get embedding
        local embedding
        if ! embedding=$(get_embedding "$text"); then
            log_warn "Failed to get embedding for chunk"
            continue
        fi
        
        # Insert into database
        if insert_into_db "$text" "$embedding" "$source_name" "$metadata"; then
            chunk_count=$((chunk_count + 1))
        fi
        
        sleep 0.2  # Rate limiting
        
    done < <(echo "$json_output" | jq -c '.[]')
    
    log_info "  Added $chunk_count chunks from $source_name"
    echo "$chunk_count"  # Output ONLY the count to stdout
}

# Get embedding from Ollama
get_embedding() {
    local text="$1"
    local escaped_text=$(echo "$text" | jq -Rs .)
    
    local response
    if ! response=$(curl -s -X POST "$OLLAMA_URL" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$EMBEDDING_MODEL\", \"prompt\": $escaped_text}" 2>/dev/null); then
        log_error "Failed to call Ollama API"
        return 1
    fi
    
    local embedding=$(echo "$response" | jq -r '.embedding // empty')
    if [[ -z "$embedding" || "$embedding" == "null" ]]; then
        log_error "No embedding in response"
        return 1
    fi
    
    echo "$embedding"
}

# Insert into PostgreSQL
insert_into_db() {
    local content="$1"
    local embedding="$2"
    local source="$3"
    local metadata="$4"
    
    # Escape single quotes for SQL
    local escaped_content=$(echo "$content" | sed "s/'/''/g")
    
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -q <<EOF
INSERT INTO training_knowledge (content, embedding, source, metadata)
VALUES (
    E'$escaped_content',
    '$embedding',
    '$source',
    '$metadata'::jsonb
);
EOF
    
    return $?
}

# Main function
main() {
    log_info "Starting knowledge base processing"
    
    check_deps || exit 1
    
    local total_chunks=0
    local processed_files=0
    local failed_files=0
    
    # Process all markdown and text files
    for file in "$KNOWLEDGE_DIR"/*.md "$KNOWLEDGE_DIR"/*.txt; do
        [[ -f "$file" ]] || continue
        [[ "$(basename "$file")" =~ ^README ]] && continue
        
        processed_files=$((processed_files + 1))
        
        local chunk_count
        if chunk_count=$(process_file "$file"); then
            total_chunks=$((total_chunks + chunk_count))
        else
            failed_files=$((failed_files + 1))
        fi
    done
    
    log_info "Processing complete"
    log_info "Files processed: $processed_files"
    log_info "Files failed: $failed_files"
    log_info "Total chunks added: $total_chunks"
}

# Run main
main
