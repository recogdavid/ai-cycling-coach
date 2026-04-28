#!/bin/bash
# Zwift Knowledge Base Builder for AI Cycling Coach

set -e  # Exit on any error

# Configuration
ZWIFT_DATA_DIR="/root/ai-cycling-coach/data/zwift-data"  # Changed directory
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

# Logging functions (same as before)
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
    
    # Check for Zwift-specific processor
    if [[ ! -f /tmp/zwift_processor.py ]]; then
        log_warn "Zwift processor not found, using generic"
        # Create a simple processor if needed
        create_zwift_processor
    fi
}

# Create a basic Zwift processor if missing
create_zwift_processor() {
    cat > /tmp/zwift_processor.py << 'EOF'
#!/usr/bin/env python3
"""
Process Zwift data files (JSON/CSV) into knowledge chunks
"""
import json
import sys
import csv
from datetime import datetime

def process_zwift_json(data):
    """Process Zwift JSON export"""
    chunks = []
    
    try:
        if isinstance(data, list):
            # Multiple rides
            for ride in data:
                chunks.extend(process_single_ride(ride))
        else:
            # Single ride
            chunks.extend(process_single_ride(data))
    except Exception as e:
        print(f"Error processing JSON: {e}", file=sys.stderr)
    
    return chunks

def process_single_ride(ride):
    """Extract insights from a single ride"""
    chunks = []
    
    # Basic ride info
    ride_id = ride.get('id', 'unknown')
    date = ride.get('start_date', '')
    duration = ride.get('duration', 0)
    distance = ride.get('distance', 0)
    avg_power = ride.get('avg_power', 0)
    avg_hr = ride.get('avg_hr', 0)
    avg_cadence = ride.get('avg_cadence', 0)
    
    # Create summary chunk
    summary = f"""
Zwift Ride Summary:
- Date: {date}
- Duration: {duration/60:.1f} minutes
- Distance: {distance:.2f} km
- Average Power: {avg_power}W
- Average Heart Rate: {avg_hr} BPM
- Average Cadence: {avg_cadence} RPM
"""
    
    chunks.append({
        "text": summary.strip(),
        "metadata": {
            "type": "ride_summary",
            "ride_id": ride_id,
            "date": date,
            "source": "zwift"
        }
    })
    
    # Power analysis chunk
    if 'power_data' in ride or 'ftp' in ride:
        ftp = ride.get('ftp', 250)  # Default FTP
        intensity = (avg_power / ftp * 100) if ftp > 0 else 0
        
        power_analysis = f"""
Power Analysis:
- FTP: {ftp}W
- Intensity: {intensity:.1f}% of FTP
- Power Zones based on this ride:
  * Zone 1 (Active Recovery): <55% FTP
  * Zone 2 (Endurance): 56-75% FTP
  * Zone 3 (Tempo): 76-90% FTP
  * Zone 4 (Threshold): 91-105% FTP
  * Zone 5 (VO2 Max): 106-120% FTP
  * Zone 6 (Anaerobic): 121-150% FTP
  * Zone 7 (Neuromuscular): >150% FTP
"""
        
        chunks.append({
            "text": power_analysis.strip(),
            "metadata": {
                "type": "power_analysis",
                "ride_id": ride_id,
                "ftp": ftp,
                "intensity_percent": intensity,
                "source": "zwift"
            }
        })
    
    # Training load/recovery
    if 'training_load' in ride:
        load = ride['training_load']
        recovery_advice = f"""
Training Load Analysis:
- Acute Training Load (ATL): {load.get('atl', 'N/A')}
- Chronic Training Load (CTL): {load.get('ctl', 'N/A')}
- Training Stress Balance (TSB): {load.get('tsb', 'N/A')}

Recovery Advice:
- If TSB is negative (-10 to -30): You're accumulating fatigue, consider a recovery day
- If TSB is near zero: Good balance, maintain current training
- If TSB is positive (+10 to +30): You're fresh, good for hard workouts
"""
        
        chunks.append({
            "text": recovery_advice.strip(),
            "metadata": {
                "type": "training_load",
                "ride_id": ride_id,
                "atl": load.get('atl'),
                "ctl": load.get('ctl'),
                "tsb": load.get('tsb'),
                "source": "zwift"
            }
        })
    
    return chunks

def process_csv_file(file_content):
    """Process CSV format Zwift data"""
    chunks = []
    reader = csv.DictReader(file_content.splitlines())
    
    rides = []
    for row in reader:
        rides.append(row)
    
    # Process as a batch or individual rides
    if len(rides) > 0:
        # Create a summary of multiple rides
        total_distance = sum(float(r.get('distance', 0)) for r in rides)
        avg_power_all = sum(float(r.get('avg_power', 0)) for r in rides) / len(rides)
        
        summary = f"""
Zwift Training Block Summary:
- Total Rides: {len(rides)}
- Total Distance: {total_distance:.2f} km
- Average Power Across Rides: {avg_power_all:.1f}W
- Date Range: {rides[0].get('date', '')} to {rides[-1].get('date', '')}
"""
        
        chunks.append({
            "text": summary.strip(),
            "metadata": {
                "type": "training_block_summary",
                "ride_count": len(rides),
                "total_distance": total_distance,
                "avg_power": avg_power_all,
                "source": "zwift_csv"
            }
        })
    
    return chunks

def main():
    """Main processing function"""
    input_data = sys.stdin.read()
    
    if not input_data.strip():
        return json.dumps([])
    
    chunks = []
    
    # Try to parse as JSON first
    try:
        data = json.loads(input_data)
        chunks = process_zwift_json(data)
    except json.JSONDecodeError:
        # Try as CSV
        chunks = process_csv_file(input_data)
    
    # Ensure we return valid JSON
    return json.dumps(chunks)

if __name__ == "__main__":
    try:
        result = main()
        print(result)
    except Exception as e:
        print(f"Error in processor: {e}", file=sys.stderr)
        print("[]")
EOF
    
    chmod +x /tmp/zwift_processor.py
    log_info "Created basic Zwift processor at /tmp/zwift_processor.py"
}

# Process a single Zwift file
process_zwift_file() {
    local file="$1"
    local source_name=$(basename "$file" | sed 's/\.[^.]*$//')
    
    log_info "Processing Zwift data: $source_name"
    
    # Get chunks from Python processor
    local json_output
    if ! json_output=$(python3 /tmp/zwift_processor.py < "$file" 2>/tmp/python_error.log); then
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
        if insert_into_db "$text" "$embedding" "zwift_$source_name" "$metadata"; then
            chunk_count=$((chunk_count + 1))
        fi
        
        sleep 0.2  # Rate limiting
        
    done < <(echo "$json_output" | jq -c '.[]')
    
    log_info "  Added $chunk chunks from $source_name"
    echo "$chunk_count"  # Output ONLY the count to stdout
}

# Get embedding from Ollama (same as before)
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

# Insert into PostgreSQL (same as before)
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
    log_info "Starting Zwift knowledge base processing"
    
    check_deps || exit 1
    
    local total_chunks=0
    local processed_files=0
    local failed_files=0
    
    # Process Zwift data files (JSON, CSV, FIT)
    for file in "$ZWIFT_DATA_DIR"/*.json "$ZWIFT_DATA_DIR"/*.csv "$ZWIFT_DATA_DIR"/*.fit; do
        [[ -f "$file" ]] || continue
        
        processed_files=$((processed_files + 1))
        
        local chunk_count
        if chunk_count=$(process_zwift_file "$file"); then
            total_chunks=$((total_chunks + chunk_count))
        else
            failed_files=$((failed_files + 1))
        fi
    done
    
    log_info "Zwift processing complete"
    log_info "Files processed: $processed_files"
    log_info "Files failed: $failed_files"
    log_info "Total chunks added: $total_chunks"
    
    # Also process any existing knowledge base files if needed
    if [[ -d "/root/ai-cycling-coach/data/knowledge-base" ]]; then
        log_info "Processing existing knowledge base files..."
        # You could call your original script here or reuse logic
    fi
}

# Run main
main
