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
    # CAPTURE ALL OUTPUT first
    local raw_output
    raw_output=$(/usr/bin/python3 /tmp/knowledge_processor.py < "$file" 2>/tmp/chunking_debug_"$(basename "$file")".log)
    local status=$?
    
# EXTREME DEBUGGING
    echo "=== EXTREME DEBUG START ===" >&2
    echo "DEBUG: Exit status: $status" >&2
    echo "DEBUG: chunks variable length: ${#chunks}" >&2
    echo "DEBUG: First 20 chars with visible control chars:" >&2
    echo -n "${chunks:0:20}" | cat -A >&2
    echo "" >&2
    echo "DEBUG: Hex dump of first 20 bytes:" >&2
    echo -n "${chunks:0:20}" | xxd >&2
    echo "=== EXTREME DEBUG END ===" >&2    
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
        echo "DEBUG: Failed to parse as JSON. First 200 chars:" >&2
        echo "${chunks:0:200}" >&2
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
EOF
}

# Main processing
process_knowledge_base() {
    check_dependencies || exit 1

    local total_chunks=0
    local processed_files=0
    local failed_files=0
    
    log INFO "🚀 Starting Knowledge Base Processing"
    
    for file in "$KNOWLEDGE_DIR"/*.md "$KNOWLEDGE_DIR"/*.txt; do
        # Skip if file doesn't exist (globbing returns pattern when no matches)
        [[ -f "$file" ]] || continue
        [[ "$(basename "$file")" =~ ^README ]] && continue
        
        processed_files=$((processed_files + 1))
        source=$(basename "$file" | sed 's/\.[^.]*$//')
        
        log INFO "📖 Processing: $source"
        
        # Smart chunking with metadata, with error handling
        local chunks
        chunks=$(smart_chunk_text "$file" "$source") || {
            log WARN "Skipping file due to chunking error: $file"
            failed_files=$((failed_files + 1))
            continue
        }
        
        # Process each chunk using process substitution to avoid subshell
        while IFS= read -r chunk; do
            text=$(echo "$chunk" | jq -r '.text')
            metadata=$(echo "$chunk" | jq -r '.metadata')
            
            # Skip empty chunks
            [[ -z "$text" ]] && continue
            
            # Generate embedding
            embedding=$(generate_embedding "$text")
            
            [[ -z "$embedding" || "$embedding" == "null" ]] && {
                log WARN "No embedding for chunk"
                continue
            }
            
            # Insert chunk
            insert_chunk "$text" "$embedding" "$source" "$metadata"
            
            total_chunks=$((total_chunks + 1))
            sleep 0.2  # Avoid overwhelming Ollama
        done < <(echo "$chunks" | jq -c '.[]')
    done
    
    log INFO "✅ Processing Complete"
    log INFO "📊 Total Files: $processed_files"
    log INFO "❌ Failed Files: $failed_files"
    log INFO "📑 Total Chunks: $total_chunks"
}

# Execute
process_knowledge_base
