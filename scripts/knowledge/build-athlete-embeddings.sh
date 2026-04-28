#!/bin/bash
#
# Athlete Embedding Builder for AI Cycling Coach
# Processes athlete data and loads into PostgreSQL with embeddings
#

set -e  # Exit on any error

# Configuration
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
echo -e "${BLUE}║   AI Cycling Coach - Athlete Embedding Builder           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

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

# Function to update athlete embedding
update_athlete_embedding() {
    local athlete_id="$1"
    local embedding="$2"

    # Update database
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << EOF
UPDATE athletes
SET embedding = '$embedding'
WHERE id = $athlete_id;
EOF
}

# Function to create athlete profile text
create_athlete_profile() {
    local athlete_id="$1"

    # Get athlete data from database
    local athlete_data=$(docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << EOF
SELECT
    name,
    gender,
    birth_date,
    weight_kg,
    ftp_watts,
    training_goal,
    event_name,
    event_location,
    training_goal_type,
    training_phase,
    phase_week,
    phase_total_weeks,
    target_event_date,
    target_event_type,
    weeks_to_event
FROM athletes
WHERE id = $athlete_id;
EOF
    )

    # Format the profile text
    echo "Athlete Profile:
ID: $athlete_id
Name: $(echo "$athlete_data" | awk 'NR==1 {print $1}')
Gender: $(echo "$athlete_data" | awk 'NR==2 {print $1}')
Age: $(echo "$athlete_data" | awk -F'[- ]' 'NR==3 {print 2024 - $3}')
Weight: $(echo "$athlete_data" | awk 'NR==4 {print $1} kg')
FTP: $(echo "$athlete_data" | awk 'NR==5 {print $1} watts')
Training Goal: $(echo "$athlete_data" | awk 'NR==6 {print $1}')
Event: $(echo "$athlete_data" | awk 'NR==7 {print $1}')
Location: $(echo "$athlete_data" | awk 'NR==8 {print $1}')
Goal Type: $(echo "$athlete_data" | awk 'NR==9 {print $1}')
Phase: $(echo "$athlete_data" | awk 'NR==10 {print $1}')
Week: $(echo "$athlete_data" | awk 'NR==11 {print $1} of $2')
Target Event: $(echo "$athlete_data" | awk 'NR==13 {print $1}')
Event Type: $(echo "$athlete_data" | awk 'NR==14 {print $1}')
Weeks to Event: $(echo "$athlete_data" | awk 'NR==15 {print $1}')
"
}

# Main processing
echo -e "${GREEN}🏃‍♂️ Processing athlete data...${NC}"
echo ""

# Get all athlete IDs - using psql with -t to remove headers and alignment
athlete_ids=$(docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT id FROM athletes;")

total_athletes=$(echo "$athlete_ids" | wc -l)
processed=0

# Process each athlete
echo "$athlete_ids" | while read -r athlete_id; do
    # Clean up the athlete_id (remove any whitespace or extra characters)
    athlete_id=$(echo "$athlete_id" | tr -d '[:space:]')

    # Skip empty lines
    if [ -z "$athlete_id" ]; then
        continue
    fi

    echo -e "${BLUE}Processing athlete ID: $athlete_id${NC}"

    # Create profile text
    profile_text=$(create_athlete_profile "$athlete_id")

    # Generate embedding
    echo -ne "  Generating embedding... "
    embedding=$(generate_embedding "$profile_text")

    if [ -z "$embedding" ] || [ "$embedding" = "null" ]; then
        echo -e "${YELLOW}SKIP (no embedding)${NC}"
        continue
    fi

    # Update database
    echo -ne "Storing... "
    update_athlete_embedding "$athlete_id" "$embedding"
    echo -e "${GREEN}✓${NC}"

    processed=$((processed + 1))

    # Small delay to not overwhelm Ollama
    sleep 0.2
done

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 ✓ Athlete Embeddings Built!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get statistics
echo -e "${BLUE}📊 Database Statistics:${NC}"
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    COUNT(*) as total_athletes,
    SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as athletes_with_embeddings
FROM athletes;
EOF

echo ""
echo -e "${GREEN}✅ Athlete embeddings are ready for RAG!${NC}"
