#!/usr/bin/env python3
import os
import json
import requests

def embed_with_ollama(text, model='nomic-embed-text'):
    """
    Generate embeddings using Ollama's embedding endpoint
    """
    try:
        response = requests.post('http://localhost:11434/api/embeddings', 
            json={
                'model': model,
                'prompt': text
            }
        )
        
        if response.status_code == 200:
            return response.json()['embedding']
        else:
            print(f"Embedding failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def process_knowledge_base(input_dir, output_dir):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all JSON files in input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f'embedded_{filename}')
            
            # Load the JSON file
            with open(input_path, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
            
            # Embed each chunk
            embedded_chunks = []
            for chunk in knowledge_base['chunks']:
                # Combine header and content for embedding
                text = f"{chunk['header']} {chunk['content']}"
                
                # Generate embedding using Ollama
                embedding = embed_with_ollama(text)
                
                if embedding:
                    embedded_chunks.append({
                        **chunk,
                        'embedding': embedding
                    })
            
            # Update knowledge base with embeddings
            knowledge_base['chunks'] = embedded_chunks
            
            # Save updated knowledge base
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, indent=2)
            
            print(f"Embedded {input_path} and saved to {output_path}")

# Directories
input_dir = '/root/ai-cycling-coach/data/processed-knowledge-base'
output_dir = '/root/ai-cycling-coach/data/embedded-knowledge-base'

# Process all knowledge base files
process_knowledge_base(input_dir, output_dir)
