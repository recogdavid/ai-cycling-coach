#!/bin/bash
set -e

# Configuration
REPO_DIR="$HOME/ai-cycling-coach"
DATE_DIR=$(date '+%Y-%m-%d')
WORKFLOWS_DIR="$REPO_DIR/workflows/$DATE_DIR"

echo "🔄 Exporting ACTIVE n8n workflows..."
echo "📁 Target: workflows/$DATE_DIR"

# Create workflows directory
mkdir -p "$WORKFLOWS_DIR"

# Export all workflows to a single file in container
docker exec ai-cycling-coach-n8n-1 n8n export:workflow --all --output=/tmp/workflows-export.json

# Copy exported file to host
docker cp ai-cycling-coach-n8n-1:/tmp/workflows-export.json /tmp/

# Parse the export file and split into individual workflow files
echo "🔍 Parsing and filtering active workflows..."
python3 << EOF
import json
import os

export_file = '/tmp/workflows-export.json'
output_dir = '$WORKFLOWS_DIR'
os.makedirs(output_dir, exist_ok=True)

# Read the export file (might be JSON array or newline-delimited JSON)
with open(export_file, 'r') as f:
    content = f.read().strip()

# Try parsing as JSON array first
try:
    workflows = json.loads(content)
    if not isinstance(workflows, list):
        workflows = [workflows]
except:
    # Try newline-delimited JSON
    workflows = []
    for line in content.split('\n'):
        if line.strip():
            try:
                workflows.append(json.loads(line))
            except:
                pass

active_count = 0
for wf in workflows:
    if wf.get('active', False):
        name = wf.get('name', 'unnamed').replace(' ', '_').replace('/', '-')
        filename = f"{output_dir}/{name}.json"
        
        with open(filename, 'w') as f:
            json.dump(wf, f, indent=2)
        
        print(f"  ✅ Exported: {name}.json")
        active_count += 1
    else:
        print(f"  ⏭️  Skipping inactive: {wf.get('name', 'unnamed')}")

print(f"\n✅ Exported {active_count} active workflows")
EOF

# Clean up temp files
rm -f /tmp/workflows-export.json
docker exec ai-cycling-coach-n8n-1 rm -f /tmp/workflows-export.json

WORKFLOW_COUNT=$(ls -1 "$WORKFLOWS_DIR"/*.json 2>/dev/null | wc -l)

if [ $WORKFLOW_COUNT -eq 0 ]; then
    echo "⚠️  No active workflows found"
    rmdir "$WORKFLOWS_DIR" 2>/dev/null || true
    exit 1
fi

echo ""
echo "📦 Summary: $WORKFLOW_COUNT active workflows saved to workflows/$DATE_DIR"

# Git operations
cd "$REPO_DIR"

# Check if git repo exists
if [ ! -d .git ]; then
    echo "⚠️  Not a git repository"
    echo "📝 Initialize with:"
    echo "   cd $REPO_DIR"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 0
fi

# Add workflows
git add workflows/$DATE_DIR/

# Check if there are changes
if git diff --staged --quiet; then
    echo "✅ No changes to commit (workflows unchanged)"
else
    # Show what changed
    echo "📝 Changes:"
    git diff --staged --name-status
    
    # Commit
    git commit -m "Export active workflows - $DATE_DIR"
    
    echo "✅ Changes committed"
    echo "📤 Push with: cd $REPO_DIR && git push"
fi

echo "🎉 Done!"
