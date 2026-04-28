#!/usr/bin/env python3
"""
Generate embeddings for training_knowledge records using nomic-embed-text via Ollama.
Uses environment variables for configuration.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    import requests
    from dotenv import load_dotenv
    from tqdm import tqdm
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install dependencies: pip install psycopg2-binary requests python-dotenv tqdm")
    sys.exit(1)

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

class EmbeddingGenerator:
    def __init__(self):
        self.setup_logging()
        self.config = self.load_config()
        self.conn = None
        
    def setup_logging(self):
        """Setup logging configuration."""
        log_file = os.getenv('LOG_FILE', 'embedding_generation.log')
        verbose = os.getenv('VERBOSE', 'true').lower() == 'true'
        
        logging.basicConfig(
            level=logging.INFO if verbose else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler() if verbose else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'database': os.getenv('DB_NAME', 'aicoach_db'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'port': int(os.getenv('DB_PORT', 5432))
            },
            'ollama': {
                'url': os.getenv('OLLAMA_URL', 'http://localhost:11434/api/embeddings'),
                'model': os.getenv('OLLAMA_MODEL', 'nomic-embed-text'),
                'timeout': int(os.getenv('OLLAMA_TIMEOUT', 60))
            }
        }
    
    def connect_db(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.config['database'])
            self.logger.info("✅ Database connection established")
            return True
        except Exception as e:
            self.logger.error(f"❌ Database connection error: {e}")
            return False
    
    def disconnect_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")
    
    def get_records_without_embeddings(self) -> List[Dict[str, Any]]:
        """Fetch records that don't have embeddings yet."""
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        query = """
            SELECT id, content, source, metadata
            FROM training_knowledge 
            WHERE embedding IS NULL
            ORDER BY id
        """
        
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            records = []
            for row in cursor.fetchall():
                records.append(dict(zip(columns, row)))
            
            cursor.close()
            return records
        except Exception as e:
            self.logger.error(f"Error fetching records: {e}")
            cursor.close()
            return []
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama nomic-embed-text model."""
        try:
            response = requests.post(
                self.config['ollama']['url'],
                json={
                    'model': self.config['ollama']['model'],
                    'prompt': text
                },
                timeout=self.config['ollama']['timeout']
            )
            response.raise_for_status()
            result = response.json()
            embedding = result.get('embedding', [])
            
            if not embedding:
                self.logger.warning(f"Empty embedding returned")
            
            return embedding
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error generating embedding: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing Ollama response: {e}")
            return []
    
    def update_embedding(self, record_id: int, embedding: List[float]) -> bool:
        """Update a record with its embedding."""
        if not self.conn:
            return False
        
        cursor = self.conn.cursor()
        
        # Convert embedding list to PostgreSQL vector string
        embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
        
        query = """
            UPDATE training_knowledge 
            SET embedding = %s::vector
            WHERE id = %s
        """
        
        try:
            cursor.execute(query, (embedding_str, record_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Error updating embedding for record {record_id}: {e}")
            return False
        finally:
            cursor.close()
    
    def check_ollama_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(
                self.config['ollama']['url'].replace('/api/embeddings', '/api/tags'),
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if self.config['ollama']['model'] in model_names:
                    self.logger.info(f"✅ Ollama is running with model {self.config['ollama']['model']}")
                    return True
                else:
                    self.logger.error(f"❌ Model {self.config['ollama']['model']} not found in Ollama")
                    self.logger.info(f"Available models: {', '.join(model_names)}")
                    return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Ollama not available: {e}")
            self.logger.info("Make sure Ollama is running: ollama serve")
            return False
    
    def run(self, dry_run: bool = False):
        """Main execution method."""
        self.logger.info("=" * 60)
        self.logger.info("Starting embedding generation")
        
        # Check Ollama availability
        if not self.check_ollama_available():
            return
        
        # Connect to database
        if not self.connect_db():
            return
        
        # Get records without embeddings
        records = self.get_records_without_embeddings()
        
        if not records:
            self.logger.info("No records found without embeddings.")
            self.disconnect_db()
            return
        
        self.logger.info(f"Found {len(records)} records without embeddings.")
        
        if dry_run:
            self.logger.info("Dry run mode - would process:")
            for record in records[:5]:
                self.logger.info(f"  ID: {record['id']}, Source: {record['source']}")
            if len(records) > 5:
                self.logger.info(f"  ... and {len(records) - 5} more")
            self.disconnect_db()
            return
        
        # Process each record with progress bar
        success_count = 0
        error_count = 0
        
        with tqdm(total=len(records), desc="Generating embeddings") as pbar:
            for record in records:
                # Generate embedding
                embedding = self.generate_embedding(record['content'])
                
                if not embedding:
                    error_count += 1
                    pbar.update(1)
                    continue
                
                # Update database
                if self.update_embedding(record['id'], embedding):
                    success_count += 1
                else:
                    error_count += 1
                
                pbar.update(1)
                time.sleep(0.2)  # Small delay
        
        # Summary
        self.logger.info("=" * 60)
        self.logger.info(f"Embedding generation complete!")
        self.logger.info(f"Total records processed: {len(records)}")
        self.logger.info(f"Successfully embedded: {success_count}")
        self.logger.info(f"Failed: {error_count}")
        
        # Final check
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM training_knowledge WHERE embedding IS NULL")
        remaining = cursor.fetchone()[0]
        cursor.close()
        
        self.logger.info(f"Records still without embeddings: {remaining}")
        self.logger.info("=" * 60)
        
        self.disconnect_db()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings for training knowledge records')
    parser.add_argument('--dry-run', action='store_true', help='Check what would be processed without making changes')
    parser.add_argument('--check-only', action='store_true', help='Check status only')
    
    args = parser.parse_args()
    
    generator = EmbeddingGenerator()
    
    if args.check_only:
        # Just check status
        if generator.connect_db():
            records = generator.get_records_without_embeddings()
            print(f"\n📊 Status Check:")
            print(f"Records without embeddings: {len(records)}")
            
            if records:
                print(f"\n📝 Sample of records needing embeddings:")
                for i, record in enumerate(records[:5], 1):
                    print(f"  {i}. ID: {record['id']}, Source: {record['source']}")
                    print(f"     Preview: {record['content'][:80]}...")
                if len(records) > 5:
                    print(f"  ... and {len(records) - 5} more")
            
            generator.disconnect_db()
    else:
        # Run generation
        generator.run(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
