import sqlite3
import json
import time
from gigachat import GigaChat
import numpy as np
from tqdm import tqdm

# GigaChat credentials
GIGACHAT_CREDENTIALS = "YWQxMDllYmQtZDA0ZC00MDM2LWEyMjktMWU1ZTJlOTViNzkyOmY2NWU0YjE2LWE0ZDctNGNlOC05M2RiLWZkZjgwZDc5YTUyYw=="

# Database path
DB_PATH = "resources/tenders.db"

# Batch size for processing
BATCH_SIZE = 128

def add_vectors_column():
    """Add vectors_gigachat column to tenders table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(tenders)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "vectors_gigachat" not in columns:
        cursor.execute("ALTER TABLE tenders ADD COLUMN vectors_gigachat BLOB")
        print("Added vectors_gigachat column to tenders table")
    else:
        print("vectors_gigachat column already exists")
    
    conn.commit()
    conn.close()

def get_tender_batches():
    """Get all tender IDs and names in batches"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total count for progress bar
    cursor.execute("SELECT COUNT(*) FROM tenders LIMIT 10")
    total_count = cursor.fetchone()[0]
    
    # Get tenders without vectors
    cursor.execute("SELECT id, name FROM tenders LIMIT 10")
    
    batches = []
    current_batch = []
    batch_ids = []
    
    for row in cursor:
        tender_id, name = row
        current_batch.append(name)
        batch_ids.append(tender_id)
        
        if len(current_batch) >= BATCH_SIZE:
            batches.append((batch_ids, current_batch))
            current_batch = []
            batch_ids = []
    
    # Add the last batch if it's not empty
    if current_batch:
        batches.append((batch_ids, current_batch))
    
    conn.close()
    return batches, total_count

def vectorize_tenders():
    """Vectorize tender names using GigaChat and store in database"""
    add_vectors_column()
    
    batches, total_count = get_tender_batches()
    
    if total_count == 0:
        print("All tenders already have vectors. Nothing to do.")
        return
    
    print(f"Vectorizing {total_count} tenders in {len(batches)} batches")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Initialize GigaChat client
    with GigaChat(
        credentials=GIGACHAT_CREDENTIALS,
        verify_ssl_certs=False
    ) as giga:
        # Process each batch with progress bar
        for batch_ids, batch_texts in tqdm(batches, desc="Processing batches"):
            try:
                # Get embeddings from GigaChat
                embeddings = giga.embeddings(batch_texts).data
                
                # Update database with embeddings
                for tender_id, embedding in zip(batch_ids, embeddings):
                    # Convert vector to binary format for SQLite BLOB storage
                    print(np.array(embedding.embedding).shape)
                    vector_blob = sqlite3.Binary(np.array(embedding.embedding).tobytes())
                    
                    # Update the database
                    cursor.execute(
                        "UPDATE tenders SET vectors_gigachat = ? WHERE id = ?",
                        (vector_blob, tender_id)
                    )
                
                conn.commit()
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing batch: {e}")
                # Continue with next batch
    
    conn.close()
    print("Vectorization complete")

if __name__ == "__main__":
    vectorize_tenders()
