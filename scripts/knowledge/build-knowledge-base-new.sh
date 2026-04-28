#!/bin/bash
#
# Enhanced Knowledge Base Builder for AI Cycling Coach
# Processes training knowledge files with smart chunking and metadata

# Configuration
KNOWLEDGE_DIR="/root/ai-cycling-coach/data/knowledge-base"
DB_CONTAINER="ai-cycling-coach-postgres-1"
DB_NAME="aicoach_db"
DB_USER="aicoach_user"
OLLAMA_URL="http://localhost:11434/api/embeddings"
EMBEDDING_MODEL="nomic-embed-text"

# Add debug/verbose mode
DEBUG=0
DRY_RUN=0

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -d|--debug) DEBUG=1 ;;
        -n|--dry-run) DRY_RUN=1 ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    case "$level" in
        INFO)
            echo -e "\e[34m[INFO $timestamp]\e[0m $message" ;;
        WARN)
            echo -e "\e[33m[WARN $timestamp]\e[0m $message" ;;
        ERROR)
            echo -e "\e[31m[ERROR $timestamp]\e[0m $message" >&2 ;;
        DEBUG)
            [[ $DEBUG -eq 1 ]] && echo -e "\e[90m[DEBUG $timestamp]\e[0m $message" ;;
    esac
}

# Dependencies check
check_dependencies() {
    local deps=("jq" "curl" "python3")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log ERROR "$dep is not installed"
            return 1
        fi
    done

    # Check Python processor script
    [ -f /tmp/knowledge_processor.py ] || {
        log ERROR "Knowledge processor script not found"
        return 1
    }
}

# Smart chunking with Python
smart_chunk_text() {
    local file="$1"
    local source="$2"
    
    log INFO "🔪 Smart Chunking: $(basename "$file")"
    
    # Add verbose error checking and logging
    local chunks
    chunks=$(/usr/bin/python3 /tmp/knowledge_processor.py < "$file" 2>/tmp/chunking_debug_"$(basename "$file")".log)
    local status=$?
    
    # Log any debug output
    if [[ -s /tmp/chunking_debug_"$(basename "$file")".log ]]; then
        log DEBUG "Chunking debug output for $file:"
        cat /tmp/chunking_debug_"$(basename "$file")".log >&2
    fi
    
    # Check processing status
    if [[ $status -ne 0 ]]; then
        log ERROR "Chunking failed for $file with exit status $status"
        return 1
    fi
    
    # Check if we got any output
    if [[ -z "$chunks" ]]; then
        log ERROR "Empty output from Python script for $file"
        return 1
    fi
    
    # Validate JSON and print
    echo "$chunks" | jq . >/dev/null 2>&1 || {
        log ERROR "Invalid JSON output for $file"
        return 1
    }
    
    # Print ONLY the JSON chunks to stdout
    echo "$chunks"
}

# Generate embedding function
generate_embedding() {
    local text="$1"
    
    # Escape text for JSON
    local escaped_text=$(echo "$text" | jq -Rs .)
    
    # Call Ollama API using the variable
    curl -s "$OLLAMA_URL" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$EMBEDDING_MODEL\", \"prompt\": $escaped_text}" \
        | jq -c '.embedding'
}

# Insert chunk into database
insert_chunk() {
    local content="$1"
    local embedding="$2"
    local source="$3"
    local metadata="$4"
    
    # Escape content for SQL
    local escaped_content=$(echo "$content" | sed "s/'/''/g")
    
    # Insert into database
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << EOF
INSERT INTO training_knowledge (content, embedding, source, metadata)
VALUES (
    E'$escaped_content',
    '$embedding',
    '$source',
    '$metadata'::jsonb
);
